from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseNotAllowed, Http404
from referenda.models import *
from django.utils import simplejson as json

def vote_frame (request, election_slug):
    try:
        election = Election.objects.get(slug=election_slug)
    except Election.DoesNotExist:
        raise Http404
    else:
        return HttpResponse(election.render_frame())

def vote_race (request, election_slug, race_slug):
    try:
        election = Election.objects.get(slug=election_slug)
        race = election.races.get(slug=race_slug)

    except Election.DoesNotExist:
        raise Http404
    except Race.DoesNotExist:
        raise Http404

    return HttpResponse(race.render())

def voter_login (request, slug):
    election = Election.objects.get(slug=slug)

    if not election.valid:
        raise Http404

    # authenticate user and return data to client
    if request.method == 'POST':
        credentials = election.authenticator.authenticate(request.POST['user_id'], request.POST['password'])

        if credentials == None:
            data = {'success': False,
                    'message': "Your username and password could not be found, or you aren't allowed to vote in this election.",
                    'races': {},}
        else:
            data = {'success': True,
                    'races': election.get_races_for(credentials.groups),}

        return HttpResponse(json.dumps(data))

    # display login front-end
    else:
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
