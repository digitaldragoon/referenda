from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.template import RequestContext
from django.core import serializers
from referenda import utils

################################################################################
# FIELDS
################################################################################

class CommaSeparatedListField(models.TextField):
    """
    Field which transparently translates between database comma-separated strings and lists of strings.
    """
    # Django likes to call to_python twice for some reason, so we hack this
    # magic string when we're on our way to the database rather than
    # to python
    MAGIC_STRING = u'\b\u0223\u0195'
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, (str, unicode)):
            if value.startswith(self.MAGIC_STRING):
                return value.lstrip(self.MAGIC_STRING)
            else:
                return value.split(',')

        elif isinstance(value, (list, tuple)):
            return value

    def get_db_prep_value(self, value):
        if isinstance(value, (str, unicode)):
            return value

        elif isinstance(value, (list, tuple)):
            return self.MAGIC_STRING + u','.join(value)

class BallotField(models.TextField):
    """
    Field which transparently translates between database strings and Python Ballot objects.
    """
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, Ballot):
            return value

        elif isinstance(value, unicode) or isinstance(value, str):
            return Ballot(value)

        else:
            raise TypeError, 'cannot translate value of type "%s" into value of type "Ballot"' % value.__class__.__name__

    def get_db_prep_value(self, value):
        if value == None:
            return ''
        
        elif isinstance(value, Ballot):
            return unicode(value)

        else:
            raise TypeError, 'value is not of type "Ballot"'

################################################################################
# MODELS
################################################################################

class PollManager (models.Manager):
    def active(self):
        return self.filter(active=True)

    def current(self):
        now = datetime.now()
        return self.active().filter(poll_opens__lte=now, poll_closes__gte=now)

    def upcoming(self):
        now = datetime.now()
        return self.active().filter(poll_opens__gte=now)

    def past(self):
        now = datetime.now()
        return self.active().filter(poll_closes__lte=now)

class Poll (models.Model):
    """
    The superclass for all types of polls.
    """
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(unique=True)
    poll_opens = models.DateTimeField(default=datetime.now()+timedelta(days=7))
    poll_closes = models.DateTimeField(default=datetime.now()+timedelta(days=14))
    active = models.BooleanField(help_text="Should this poll open? (disable to make changes before re-opening poll)", default=True)
    inactive_notice = models.TextField(help_text="Message to display when the polls have opened but the poll has been marked as inactive. Use this to announce period of maintenance or repair.", blank=True)
    ballot = BallotField(blank=True)
    administrator = models.ForeignKey(User)

    objects = PollManager()

    _child_type = models.CharField(max_length=30, editable=False)
    def _get_child(self):
        """
        Automatically handles link to child implementing class.
        """
        try:
            return getattr(self, self._child_type.lower())
        except:
            raise AttributeError('unknown child type %s for Poll %s' % (self._child_type, self.__unicode__()))
    child = property(_get_child)

    def __unicode__(self):
        return self.name

    def generate_ballot (self):
        """
        Create a ballot from the parameters of the poll. Subclasses must implement this.
        """
        raise NotImplementedError, "subclasses must implement generate_ballot()"

    def _get_days_delta (self, then):
        delta = then - datetime.now()
        return delta.days

    def _get_hours_delta (self, then):
        delta = then - datetime.now()
        return (delta.seconds % 86400) / 3600

    def _get_minutes_delta (self, then):
        delta = then - datetime.now()
        return (delta.seconds % 3600) / 60

    def _get_days_remaining(self):
        return self._get_days_delta(self.poll_closes)
    days_remaining = property(_get_days_remaining)

    def _get_hours_remaining (self):
        return self._get_hours_delta(self.poll_closes)
    hours_remaining = property(_get_hours_remaining)

    def _get_minutes_remaining (self):
        return self._get_hours_delta(self.poll_closes)
    minutes_remaining = property(_get_minutes_remaining)

    def _get_days_until(self):
        return self._get_days_delta(self.poll_opens)
    days_until = property(_get_days_until)

    def _get_hours_until (self):
        return self._get_hours_delta(self.poll_opens)
    hours_until = property(_get_hours_until)

    def _get_minutes_until (self):
        return self._get_minutes_delta(self.poll_opens)
    minutes_until = property(_get_minutes_until)

    def _get_is_current (self):
        now = datetime.now()
        return now < self.poll_closes and now >= self.poll_opens
    is_current = property(_get_is_current)

    def _get_is_upcoming (self):
        now = datetime.now()
        return now < self.poll_opens
    is_upcoming = property(_get_is_upcoming)

    def _get_is_past (self):
        now = datetime.now()
        return now >= self.poll_closes
    is_past = property(_get_is_past)

    def save(self):
        self._child_type = self.__class__.__name__
        super(Poll, self).save()

    class Meta:
        ordering = ['-poll_opens',]

class Election (Poll):
    """
    Election with heavy encryption and all sorts of other security features.
    """
    authentication = models.CharField(max_length=200, choices=utils.get_auth_choices())
    objects = PollManager()

    def _get_authenticator(self):
        if hasattr(self, '_authenticator'):
            return self._authenticator
        else:
            modname = self.authentication.rsplit('.', 1)[0]
            classname = self.authentication.rsplit('.', 1)[1]

            mod = __import__(modname, {}, {}, [''])
            self._authenticator = getattr(mod, classname)()

            return self._authenticator

    authenticator = property(_get_authenticator)

    def _compute_hash(self):
        """
        Computes a hash of this Election.
        """
        #FIXME
        raise NotImplementedError, "not yet implemented"
    hash = property(_compute_hash)

    def _check_approval(self):
        """
        Check whether this election has been approved by all of its election authorities.
        """
        if self.authorities.count() <= 0:
            return False
        else:
            is_approved = True
            for authority in self.authorities.all():
                is_approved = authority.approved and is_approved
    
            return is_approved
    approved = property(_check_approval)

    def _check_signatures(self):
        """
        Check whether all election authorities have signed the empty ballot.
        """
        #FIXME
        return True

        if self.ballot == "":
            # if we have no ballot, it cannot be signed
            return False

        elif self.authorities.count() <= 0:
            return False
        else:
            is_signed = True
            for authority in self.authorities.all():
                is_signed = authority.has_valid_signature and is_signed

            return is_signed
    signed = property(_check_signatures)

    def _check_validity(self):
        """
        Determines whether this Election is valid - that is, whether its ElectionAuthorities have approved and properly signed it. Only valid elections may have ballots cast in them.
        """
        return self.approved and self.signed
    valid = property(_check_validity)

    def get_races_for (self, groups):
        """
        Given a list of groups, returns a list of races which have any one of those groups in their 'groups' field, or which have no groups in thier 'groups' field.
        """
        final_races = []
        for race in self.races.all():
            valid_race = False
            if len(race.groups) == 0:
                valid_race = True
            else:
                for group in groups:
                    if race.groups.count(group) > 0:
                        valid_race = True
                        break

            if valid_race:
                final_races.append(race.pk)

        return serializers.serialize('python', self.races.filter(pk__in=final_races), fields=('name', 'slug', 'num_choices'))

    def _get_is_submissible (self):
        return self.is_current and self.active and self.valid 
    is_submissible = property(_get_is_submissible)

class ElectionAuthority (models.Model):
    """
    An administrator who acts as a validator and tabulator of an Election, but cannot set the parameters of an Election.
    """
    user = models.ForeignKey(User)
    election = models.ForeignKey(Election, related_name="authorities")
    public_key = models.TextField(blank=True)
    election_signature = models.TextField(blank=True)
    ballot_signature = models.TextField(blank=True)
    approved = models.BooleanField(default=False)

    def _verify_signature(self):
        """
        Verifies this ElectionAuthority's ballot and election signatures against the hashes of the Ballot and Election.
        """
        #FIXME
        return True
    has_valid_signature = property(_verify_signature)

    def __unicode__(self):
        return '%s %s [%s]' % (self.user.first_name, self.user.last_name, self.election)

    class Meta:
        verbose_name = "Election Authority"
        verbose_name_plural = "Election Authorities"
        ordering = ['user']
        unique_together = ('user', 'election')

class RaceManager (models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return super(RaceManager, self).get_query_set().order_by('rank')

class Race (models.Model):
    """
    A race for an individual position, such as a senate seat or board chairmanship.
    """
    name = models.CharField(max_length=250)
    slug = models.SlugField()
    election = models.ForeignKey(Election, related_name="races")
    num_choices = models.PositiveIntegerField(default=1)
    rank = models.PositiveIntegerField()
    groups = CommaSeparatedListField(blank=True)

    objects = RaceManager()

    def __unicode__(self):
        return "%s [%d, %s]" % (self.name, self.rank, self.election)

    def num_choices_iter(self):
        return range(self.num_choices)

    class Meta:
        ordering = ['election', 'name']
        unique_together = ('slug', 'election',)

class Referendum (models.Model):
    """
    A referendum on a particular issue, such as changes to formal documents or a ballot proposition.
    """
    name = models.CharField(max_length=250)
    text = models.TextField()
    election = models.ForeignKey(Election, related_name="referendums")

    def __unicode__(self):
        return "%s [%s]" % (self.name, self.election)

    class Meta:
        ordering = ['election', 'name']

class Candidate (models.Model):
    """
    The superclass for candidates in Races.
    """
    race = models.ForeignKey(Race, related_name="candidates")

    template = 'referenda/ballotcandidate.html'

    _child_type = models.CharField(max_length=30, editable=False)
    def _get_child(self):
        """
        Automatically handles link to child implementing class.
        """
        try:
            return getattr(self, self._child_type.lower())
        except:
            raise AttributeError('unknown child type %s for Candidate %s' % (self._child_type, self.__unicode__()))
    child = property(_get_child)

    def __unicode__(self):
        return self.pk

    def save(self):
        self._child_type = self.__class__.__name__
        super(Candidate, self).save()

    class Meta:
        ordering = ['race',]

class BallotCandidate (Candidate):
    """
    A Candidate which has a formal place on the ballot.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=1000, blank=True)

    def _get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)
    full_name = property(_get_full_name)

    def __unicode__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Ballot Candidate'
        ordering = ['race', 'last_name', 'first_name']

try:
    from photologue import models as photologue
    class BallotCandidatePhoto (photologue.ImageModel):
        candidate = models.OneToOneField(BallotCandidate, related_name='photo')
except ImportError:
    pass

class WriteInCandidate (Candidate):
    """
    A write-in candidate for a Race.
    """
    name = models.CharField(max_length=250)

    template = 'referenda/ballotcandidate.html'

    def _get_full_name(self):
        return name
    full_name = property(_get_full_name)

    def __unicode__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Write-in Candidate'
        ordering = ['race', 'name']

class SealedVote (models.Model):
    """
    A finished vote uploaded by a voter.
    """
    user_id = models.CharField(max_length=100)
    public_key = models.TextField()
    poll = models.ForeignKey(Poll, related_name='sealedvotes')
    ballot = BallotField()
    signature = models.TextField()
    timestamp = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return '%s [%s]' % (self.user_id, self.poll)

    class Meta:
        unique_together = ('user_id', 'poll')
    
class Ballot (unicode):
    """
    A string representation of an Election ballot. Note that ballots are immutable. Polls should be responsible for the code that generates a given ballot.
    """

    def _compute_hash(self):
        """
        Computes the hash of this ballot for signing.
        """
        #FIXME
        raise NotImplementedError, "not yet implemented"
    hash = property(_compute_hash)

    class Meta:
        abstract = True
