from datetime import datetime
from django.db import models

class Poll (models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField()
    poll_opens = models.DateTimeField(default=datetime.now())
    poll_closes = models.DateTimeField(default=datetime.now())
    active = models.BooleanField(help_text="Should this poll open? (disable to make changes before re-opening poll)", default=True)
    empty_ballot = models.TextField(blank=True)

    # Automatically handles link to child implementing class
    _child_type = models.CharField(max_length=30, editable=False)
    def _get_child(self):
        try:
            return getattr(self, self._child_type.lower())
        except:
            raise Exception('unknown child type %s for Poll %s' % (self._child_type, self.__unicode__()))
    child = property(_get_child)

    def __unicode__(self):
        return self.name

    def save(self):
        self._child_type = self.__class__.__name__
        super(Poll, self).save()

    class Meta:
        ordering = ['-poll_opens',]

class Election (Poll):
    pass

class ElectionAuthority (models.Model):
    user_id = models.CharField(max_length=100)
    public_key = models.TextField()
    election = models.ForeignKey(Election, related_name="authorities")
    approved = models.BooleanField()

class Race (models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField()
    election = models.ForeignKey(Election, related_name="races")

    def __unicode__(self):
        return "%s [%s]" % (self.name, self.election)

    class Meta:
        ordering = ['election', 'name']

class Referendum (models.Model):
    name = models.CharField(max_length=250)
    text = models.TextField()
    election = models.ForeignKey(Election, related_name="referendums")

    def __unicode__(self):
        return "%s [%s]" % (self.name, self.election)

    class Meta:
        ordering = ['election', 'name']

class Candidate (models.Model):
    race = models.ForeignKey(Race, related_name="candidates")

    # Automatically handles link to child implementing class
    _child_type = models.CharField(max_length=30, editable=False)
    def _get_child(self):
        try:
            return getattr(self, self._child_type.lower())
        except:
            raise Exception('unknown child type %s for Candidate %s' % (self._child_type, self.__unicode__()))
    child = property(_get_child)

    def _get_full_name(self):
        raise NotImplementedError, "call this method on the child class"
    full_name = property(_get_full_name)

    def __unicode__(self):
        return self.full_name

    def save(self):
        self._child_type = self.__class__.__name__
        super(Candidate, self).save()

    class Meta:
        ordering = ['race',]

class BallotCandidate (Candidate):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=500)

    def _get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    class Meta:
        ordering = ['race', 'full_name']

class WriteInCandidate (Candidate):
    name = models.CharField(max_length=250)

    def _get_full_name(self):
        return name

    class Meta:
        ordering = ['race', 'full_name']
    
class Ballot (models.Model):
    user_id = models.CharField(max_length=100)
    poll = models.ForeignKey(Poll)
    data = models.TextField()
    signature = models.TextField()
