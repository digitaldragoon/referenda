from django.test import TestCase
from referenda.models import *

class CandidateTestCase(TestCase):
    fixtures = ['test_data',]

    def testChildLink(self):
        candidate = Candidate.objects.get(pk=1)
        self.assert_(isinstance(candidate.child, BallotCandidate))
