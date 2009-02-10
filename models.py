from datetime import datetime
from django.db import models

################################################################################
# FIELDS
################################################################################

class BallotField(models.TextField):
    """
    Field which transparently translates between database strings and Python Ballot objects.
    """

    def to_python(self, value):
        if isinstance(value, Ballot):
            return value

        elif isinstance(value, str):
            return Ballot(value)

        else:
            raise TypeError, 'cannot translate value into type Ballot'

################################################################################
# MODELS
################################################################################

class Poll (models.Model):
    """
    The superclass for all types of polls.
    """
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField()
    poll_opens = models.DateTimeField(default=datetime.now())
    poll_closes = models.DateTimeField(default=datetime.now())
    active = models.BooleanField(help_text="Should this poll open? (disable to make changes before re-opening poll)", default=True)
    inactive_notice = models.TextField(help_text="Message to display when the polls have opened but the poll has been marked as inactive. Use this to announce period of maintenance or repair.", blank=True)
    empty_ballot = BallotField(blank=True)

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

    def save(self):
        self._child_type = self.__class__.__name__
        super(Poll, self).save()

    class Meta:
        ordering = ['-poll_opens',]

class Election (Poll):
    """
    Election with heavy encryption and all sorts of other security features.
    """

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
        if self.empty_ballot == "":
            # if we have no ballot, it cannot be signed
            return False

        elif self.authorities.count() <= 0:
            return False
        else:
            is_signed = True
            for authority in self.authorities.all():
                is_signed = authority.has_valid_signature and is_signed

            return is_signed
    signed = property(_check_approval)

    def _check_validity(self):
        """
        Determines whether this Election is valid - that is, whether its ElectionAuthorities have approved and properly signed it. Only valid elections may have ballots cast in them.
        """
        return self.approved and self.signed
    valid = property(_check_validity)


class ElectionAuthority (models.Model):
    """
    An administrator who acts as a validator and tabulator of an Election, but cannot set the parameters of an Election.
    """

    user_id = models.CharField(max_length=100)
    public_key = models.TextField()
    election = models.ForeignKey(Election, related_name="authorities")
    election_signature = models.TextField()
    ballot_signature = models.TextField()
    approved = models.BooleanField()

    def _verify_signature(self):
        """
        Verifies this ElectionAuthority's ballot and election signatures against the hashes of the Ballot and Election.
        """
        #FIXME
        raise NotImplementedError, "not yet implemented"
    has_valid_signature = property(_verify_signature)

    def __unicode__(self):
        return '%s [%s]' % (self.user_id, self.election)

    class Meta:
        verbose_name = "Election Authority"
        verbose_name_plural = "Election Authorities"
        ordering = ['user_id',]

class Race (models.Model):
    """
    A race for an individual position, such as a senate seat or board chairmanship.
    """
    name = models.CharField(max_length=250)
    slug = models.SlugField()
    election = models.ForeignKey(Election, related_name="races")

    def __unicode__(self):
        return "%s [%s]" % (self.name, self.election)

    class Meta:
        ordering = ['election', 'name']

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
    bio = models.CharField(max_length=500)

    def _get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)
    full_name = property(_get_full_name)

    def __unicode__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Ballot Candidate'
        ordering = ['race', 'last_name', 'first_name']

class WriteInCandidate (Candidate):
    """
    A write-in candidate for a Race.
    """
    name = models.CharField(max_length=250)

    def _get_full_name(self):
        return name
    full_name = property(_get_full_name)

    def __unicode__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Write-in Candidate'
        ordering = ['race', 'name']
    
class Ballot (str):
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

class SealedVote (models.Model):
    """
    A finished vote uploaded by a voter.
    """
    user_id = models.CharField(max_length=100)
    poll = models.ForeignKey(Poll)
    ballot = models.TextField()
    signature = models.TextField()
