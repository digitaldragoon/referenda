from django.db import models
from referenda.models import Ballot

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

