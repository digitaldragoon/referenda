from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseNotAllowed
from referenda.models import *

def voter_login (request, slug):
    if request.method == 'POST':
        return HttpResponse()
    else:
        election = Election.objects.get(slug=slug)
        return render_to_response('referenda/voter_login.html', 
                              locals(),
                              context_instance=RequestContext(request))

def home (request):
    page_title = 'Home'

    current_elections = Election.objects.current()
    upcoming_elections = Election.objects.upcoming()
    past_elections = Election.objects.past()
    return render_to_response('referenda/home.html', 
                              locals(),
                              context_instance=RequestContext(request))
