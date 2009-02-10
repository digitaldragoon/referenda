from django.test import TestCase
from referenda.models import *

class CandidateTestCase(TestCase):
    fixtures = ['test_data',]

    def testChildLink(self):
        # should get a BallotCandidate in this case
        candidate = Candidate.objects.get(pk=1)
        self.assert_(isinstance(candidate.child, BallotCandidate))

        # create a couple more candidates
        race = Race.objects.get(slug='my-race')
        a = BallotCandidate(first_name="John", last_name="Smith", race=race)
        b = BallotCandidate(first_name="Jane", last_name="Doe", race=race)
        c = WriteInCandidate(name="John Q. Public", race=race)
        a.save()
        b.save()
        c.save()

        # iterate over the candidates again
        self.assert_(isinstance(race.candidates.all()[1].child, BallotCandidate))
        self.assert_(isinstance(race.candidates.all()[2].child, BallotCandidate))
        self.assert_(isinstance(race.candidates.all()[3].child, WriteInCandidate))


class ElectionTestCase(TestCase):
    fixtures = ['test_data',]

    def testApproval(self):
        # election should not be approved
        election = Election.objects.get(slug='my-election')
        self.assert_(not election.approved)

        # get this election's authority, and approve the election
        authority = election.authorities.all()[0]
        authority.approved = True
        authority.save()

        # election is now approved
        self.assert_(election.approved)

class BallotFieldTestCase(TestCase):
    fixtures = ['test_data',]

    def testObjectRelationalMapping(self):
        # putting a Ballot in the database
        election = Election.objects.get(slug='my-election')
        election.ballot = Ballot('absolutelybogushashcode')
        election.save()
        
        # retrieve it from the database again
        election = Election.objects.get(slug='my-election')
        self.assert_(isinstance(election.ballot, Ballot))
        self.assertEqual(election.ballot, u'absolutelybogushashcode')
