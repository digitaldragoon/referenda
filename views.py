from django.shortcuts import render_to_response
from django.template import RequestContext
from referenda.models import *

def home (request):
    page_title = 'Home'

    current_elections = Election.objects.current()
    upcoming_elections = Election.objects.upcoming()
    past_elections = Election.objects.past()
    return render_to_response('referenda/home.html', 
                              locals(),
                              context_instance=RequestContext(request))
