from django.test import TestCase
from referenda.models import *

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
