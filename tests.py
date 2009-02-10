from django.test import TestCase
from referenda.models import *

class CandidateTestCase(TestCase):
    fixtures = ['candidate_data',]

    def testChildLink(self):
        candidate = Candidate.objects.get(pk=1)
        self.assert_(isinstance(candidate.child, BallotCandidate))

class ElectionTestCase(TestCase):
    fixtures = ['election_data',]

    def testApproval(self):
        election = Election.objects.get(pk=1)
        self.assert_(election.approved)
