from django.db import transaction
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseNotAllowed, Http404
from django.core import serializers
from django.utils import simplejson as json
from referenda.models import *
from referenda.forms import *
from referenda.crypto import utils as cryptoutils

def preview (request, election_slug):

    try:
        election = Election.objects.get(slug=election_slug)
    except Election.DoesNotExist:
        raise Http404
    else:
        elgamal_json_params = '{}'
        page_title = '%s (PREVIEW BALLOT)' % election
        return render_to_response('referenda/preview.html',
                                  locals(),
                                  context_instance=RequestContext(request))

def trustee (request, election_slug):
    try:
        election = Election.objects.get(slug=election_slug)
    except Election.DoesNotExist:
        raise Http404
    else:
        return render_to_response('referenda/trustee.html',
                                  locals(),
                                  context_instance=RequestContext(request))

def booth (request, election_slug):
    from referenda.auth.standard import *
    election = Election.objects.get(slug=election_slug)

    if not election.is_submissible:
        raise Http404

    # authenticate user and return data to client
    if request.method == 'POST':
        if not election.has_voted(request.POST['user_id']):
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
                    data = {
                        'status': 'success',
                        'friendlyName': credentials.friendly_name,
                        'election': {
                            'pk': election.public_key,
                            'races': serializers.serialize('python', election.races.all(), fields=('name', 'slug', 'num_choices')),
                            'eligibleRaces': serializers.serialize('python', election.get_races_for(credentials.groups), fields=('slug')),
                            },
                        }
        else:
                data = {'status': 'duplicate',
                        'message': "You have already voted in this election.",}

        return HttpResponse(json.dumps(data))

    # display login front-end
    else:
        elgamal_json_params = json.dumps(cryptoutils.ELGAMAL_PARAMS.toJSONDict(), sort_keys=True)
        return render_to_response('referenda/booth.html', 
                              locals(),
                              context_instance=RequestContext(request))

def javascript_template (request, election_slug, template_name):
    try:
        election = Election.objects.get(slug=election_slug)
    except Election.DoesNotExist:
        raise Http404
    else:
        return render_to_response('referenda/js/%s.html' % template_name, locals(), context_instance=RequestContext(request));

@transaction.commit_manually
def submit_ballot (request, election_slug):
    if request.method == 'POST':
        try:
            election = Election.objects.get(slug=election_slug)
        except Election.DoesNotExist:
            raise Http404
        else:
            if election.is_submissible:
                credentials = election.authenticator.authenticate(request.POST['user_id'], request.POST['password'])
                if election.has_voted(request.POST['user_id']):
                    response = {
                        'status': 'duplicate',
                        'message': 'You have already voted in this election.',
                    }

                    transaction.rollback()
                    return HttpResponse(json.dumps(response))

                elif credentials != None:

                    ballots = json.loads(request.POST['ballot'])

                    # verify this voter is allowed to vote in all races
                    eligible_races = election.get_races_for(credentials.groups)
                    eligible_slugs = [x.slug for x in eligible_races]

                    for key in ballots:
                        data = {
                            'user_id': request.POST['user_id'],
                            'race': election.races.get(slug=key).pk,
                            'ballot': ballots[key],
                        }

                        form = SealedVoteForm(data)

                        if form.is_valid() and eligible_slugs.count(key) > 0:
                            form.save()
                        else:
                            response = {
                                'status': 'invalid',
                                'message': 'The vote sent to the server was corrupted. Please try submitting again.',
                            }

                            transaction.rollback()
                            return HttpResponse(json.dumps(response))

                    # if we made it this far, all the forms check out
                    response = {
                        'status': 'success',
                        'message': 'Your ballot was successfully submitted.',
                    }

                    transaction.commit()
                    return HttpResponse(json.dumps(response))

                else:
                    response = {
                        'status': 'forbidden',
                        'message': 'Your username and password did not authenticate successfully.',
                    }

                    transaction.rollback()
                    return HttpResponse(json.dumps(response))


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
