from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.template import RequestContext
from django.core.exceptions import *
from django.core import serializers
from django.utils import simplejson as json
from referenda import utils

################################################################################
# FIELDS
################################################################################

class CommaSeparatedListField(models.TextField):
    """
    Field which transparently translates between database comma-separated strings and lists of strings.
    """
    # Django likes to call to_python twice when saving to the database for some
    # reason, so we tack this magic string onto the front when we're on our way
    # to the database rather than to python. This allows us to identify whether
    # we should pass the string through to the database or create a list from it
    # for use in the code.
    MAGIC_STRING = u'\b\u0223\u0195cq.;*}Dhc=#%(iM(9s]\\w#\']u?,$08 8G/v(6967W%'
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
        return self._get_minutes_delta(self.poll_closes)
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

    ORDER_CHOICES = (
            ('random', 'Random'),
            ('alphabetical', 'Alphabetical'),
            ('default', 'As added'),
        )

    order = models.CharField(max_length=50, choices=ORDER_CHOICES)
    authentication = models.CharField(max_length=200, choices=utils.get_auth_choices())
    public_key = models.TextField(blank=True)

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

    def _check_validity(self):
        """
        Check whether all election authorities have signed the empty ballot, and ensures that one of the election authorities is listed as possesing this election's public key.
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
    valid = property(_check_validity)

    def get_races_for (self, groups):
        """
        Given a list of groups, returns a QuerySet of races which have any one of those groups in their 'groups' field, or which have no groups in thier 'groups' field.
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

        return self.races.filter(pk__in=final_races)

    def _get_is_submissible (self):
        return self.is_current and self.active and self.valid 
    is_submissible = property(_get_is_submissible)

    def _get_parameters (self):
        parameters = {}

        parameters['races'] = serializers.serialize('python', election.races.all(), fields=('name', 'slug', 'num_choices'))
        parameters['pk'] = self.public_key

        return json.dumps(parameters)

    parameters = property(_get_parameters)

    def has_voted(self, user_id):
        for race in self.races.all():
            if race.sealedvotes.filter(user_id=user_id).count() > 0:
                return True

        return False

class ElectionAuthority (models.Model):
    """
    An administrator who acts as a validator and tabulator of an Election, but cannot set the parameters of an Election.
    """
    user = models.ForeignKey(User)
    election = models.ForeignKey(Election, related_name="authorities")
    public_key = models.TextField(blank=True)
    election_signature = models.TextField(blank=True)

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

    def ordered_candidates(self):
        return getattr(self.candidates, self.election.order)()

    class Meta:
        ordering = ['election', '-rank', 'name']
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

class CandidateManager (models.Manager):
    use_for_related_fields = True

    def random(self):
        return self.order_by('?')

    def alphabetical(self):
        return self.order_by('last_name', 'first_name')

    def default(self):
        return self.order_by('pk')

class Candidate (models.Model):
    """
    A candidate with a formal place on a ballot.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=1000, blank=True)
    race = models.ForeignKey(Race, related_name="candidates")

    objects = CandidateManager()

    template = 'referenda/candidate.html'

    def _get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)
    full_name = property(_get_full_name)

    def __unicode__(self):
        return self.full_name

    def save(self):
        self._child_type = self.__class__.__name__
        super(Candidate, self).save()

    class Meta:
        ordering = ['race', 'last_name', 'first_name']

try:
    from photologue import models as photologue
    class CandidatePhoto (photologue.ImageModel):
        candidate = models.OneToOneField(Candidate, related_name='photo')
except ImportError:
    pass

class SealedVote (models.Model):
    """
    A finished vote uploaded by a voter.
    """
    user_id = models.CharField(max_length=100)
    race = models.ForeignKey(Race, related_name='sealedvotes')
    ballot = BallotField()
    timestamp = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return '%s [%s]' % (self.user_id, self.race)

    def save (self):
        if self.race.election.is_submissible:
            super(SealedVote, self).save()
        else:
            raise PermissionDenied, 'election is not currently accepting votes.'

    class Meta:
        unique_together = ('user_id', 'race')
    
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

    def block(self):
        """
        Outputs the ballot as a block of text with line breaks suitable for rendering out to a page.
        """
        line_length = 50
        sets = int(len(self)/line_length)
        blockstring = ''
        for i in range(sets):
            blockstring += self[line_length*i:line_length*(i+1)] + '<br/>'
        blockstring += self[line_length*sets:]

        return blockstring

    class Meta:
        abstract = True
