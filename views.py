from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseNotAllowed, Http404
from referenda.models import *
from django.utils import simplejson as json
from referenda.forms import *

def vote_test (request, slug):
    try:
        election = Election.objects.get(slug=slug)
    except Election.DoesNotExist:
        raise Http404
    else:
        return render_to_response('referenda/vote_test.html',
                                  locals(),
                                  context_instance=RequestContext(request))

def vote_content (request, slug):
    try:
        election = Election.objects.get(slug=slug)
    except Election.DoesNotExist:
        raise Http404
    else:
        return render_to_response('referenda/vote_content.html',
                                  locals(),
                                  context_instance=RequestContext(request))

def voter_login (request, slug):
    from referenda.auth.standard import *
    election = Election.objects.get(slug=slug)

    if not election.is_submissible:
        raise Http404

    # authenticate user and return data to client
    if request.method == 'POST':
        if election.sealedvotes.filter(user_id=request.POST['user_id']).count() == 0:
            try:
                credentials = election.authenticator.authenticate(request.POST['user_id'], request.POST['password'])
            except InvalidCredentials:
                data = {'status': 'invalid',
                        'message': "The username and password you entered were not valid.",}
            except Unauthorized:
                data = {'status': 'forbidden',
                        'message': "You are not allowed to vote in this election.",}
            else:

                if credentials == None:
                    data = {'status': 'invalid',
                            'message': "Your username and password could not be found, or you are not allowed to vote in this election.",}
                else:
                    data = {'status': 'success',
                            'friendly_name': credentials.friendly_name,
                            'user_id': credentials.user_id,
                            'races': election.get_races_for(credentials.groups),}
        else:
                data = {'status': 'duplicate',
                        'message': "You have already voted in this election.",}

        return HttpResponse(json.dumps(data))

    # display login front-end
    else:
        return render_to_response('referenda/voter_login.html', 
                              locals(),
                              context_instance=RequestContext(request))

def submit_ballot (request, slug):
    if request.method == 'POST':
        try:
            election = Election.objects.get(slug=slug)
        except Election.DoesNotExist:
            raise Http404
        else:
            if election.is_submissible:

                form = SealedVoteForm(request.POST)

                if form.is_valid():
                    if election.authenticator.authenticate(form.cleaned_data['user_id'], request.POST['password']) != None:
                        if election.sealedvotes.filter(user_id=form.cleaned_data['user_id']).count() <= 0:
                            obj = form.save(commit=False)
                            obj.poll = election
                            obj.save()

                            response = {
                                'status': 'success',
                                'message': 'Your ballot was successfully submitted.',
                                #FIXME: return when implemented
                                #'receipt': obj.ballot.hash,
                            }
                            return HttpResponse(json.dumps(response))
                        else:
                            response = {
                                'status': 'duplicate',
                                'message': 'You have already voted in this election.',
                            }
                            return HttpResponse(json.dumps(response))
                    else:
                        response = {
                            'status': 'forbidden',
                            'message': 'Your username and password did not authenticate successfully.',
                        }
                        return HttpResponse(json.dumps(response))
                else:
                    response = {
                        'status': 'invalid',
                        'message': 'The vote sent to the server was corrupted. Please try submitting again.',
                    }
                    return HttpResponse()
            else:
                raise Http404
    else:
        return HttpResponseNotAllowed(['POST',])

def home (request):
    page_title = 'Home'

    current_elections = Election.objects.current()
    upcoming_elections = Election.objects.upcoming()
    past_elections = Election.objects.past()
    return render_to_response('referenda/home.html', 
                              locals(),
                              context_instance=RequestContext(request))
