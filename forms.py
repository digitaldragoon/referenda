from django import forms
from referenda.models import *

class SealedVoteForm (forms.ModelForm):
    
    class Meta:
        model = SealedVote
        exclude = ('poll',)
