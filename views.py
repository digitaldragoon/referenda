from django.db import transaction
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseNotAllowed, Http404
from django.core import serializers
from django.utils import simplejson as json
from django.contrib.auth import authenticate
from referenda.models import *
from referenda.forms import *
from referenda.crypto import utils as cryptoutils

import struct
import operator
from referenda.crypto import algs

def election_detail (request, slug):
    try:
        election = Election.objects.get(slug=slug)
    except Election.DoesNotExist:
        raise Http404
    else:
        if election.is_tallied:
            races = election.races.all()

            for race in races:
                tallydict = {}
                total = 0

                for ballot in race.unsealedvotes.all():
                    total += 1
                    if tallydict.has_key(ballot.vote):
                        tallydict[ballot.vote] += 1;
                    else:
                        tallydict[ballot.vote] = 1;

                race.votes = sorted(tallydict.items(), key=operator.itemgetter(1))
                race.votes.reverse()
                race.votes = [(x[0], x[1], x[1]/float(total)*100, int(x[1]/float(total)*100)) for x in race.votes]

        return render_to_response('referenda/election_detail.html',
                                  locals(),
                                  context_instance=RequestContext(request))


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
        if election.is_tallied:
            raise Http404

        if request.method == 'POST':
            try:
                authority = election.authorities.get(user__username=request.POST['user_id'])
            except User.DoesNotExist:
                data = {'status': 'forbidden',
                        'message': "You are not an election authority in this election.",}
            else:
                user = authenticate(username=request.POST['user_id'], password=request.POST['password'])

                if user != None:
                    data = {'status': 'success',
                            'races': [x['slug'] for x in election.races.all().values('slug')]
                           }

                else:
                    data = {'status': 'invalid',
                            'message': 'The username and password you entered were not valid.',}


            return HttpResponse(json.dumps(data))

        else:
            return render_to_response('referenda/trustee.html',
                                  locals(),
                                  context_instance=RequestContext(request))

@transaction.commit_manually
def submit_tally (request, election_slug):
    def decode_string(string):
        value = int(string)
        hex = '%X' % value

        plainstring = ''

        i = 0
        while i < len(hex):
            plainstring += chr(int(hex[i:i+2], 16))
            i += 2

        return plainstring.strip('\0"')

    try:
        election = Election.objects.get(slug=election_slug)
    except Election.DoesNotExist:
        transaction.rollback()
        raise Http404
    else:
        if request.method == 'POST':

            if election.is_tallied or election.stage != 'tally':
                raise Http404

            data = json.loads(request.POST['data'])

            for race in data:
                ballots = data[race]
                race_obj = election.races.get(slug=race)
            
                for ballot in ballots:
                    receipt = decode_string(ballot['receipt'])
                    if len(receipt) > 40:
                        raise Exception, '+++' + receipt[40] + '+++'

                    for answer in ballot['answers']:
                        plain_answer = decode_string(answer)
                        if plain_answer != 'None':
                            vote = UnsealedVote(race=race_obj, receipt=receipt, vote=decode_string(answer))
                            vote.save()

                    transaction.commit()

            election.is_tallied = True
            election.save()
            transaction.commit()
            return HttpResponse(json.dumps({'status': 'success'}), mimetype='application/json')

        else:
            transaction.rollback()
            return HttpResponseNotAllowed(['POST',])

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
            except Unavailable:
                data = {'status': 'unavailable',
                        'message': "The authentication service is currently down. Please try again later.",}
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

def javascript_template (request, election_slug, type, template_name):
    try:
        election = Election.objects.get(slug=election_slug)
    except Election.DoesNotExist:
        raise Http404
    else:
        return render_to_response('referenda/js/%s/%s.html' % (type, template_name), locals(), context_instance=RequestContext(request));

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
                    return HttpResponse(json.dumps(response), mimetype='application/json')

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
                            return HttpResponse(json.dumps(response), 'application/json')

                    # if we made it this far, all the forms check out
                    response = {
                        'status': 'success',
                        'message': 'Your ballot was successfully submitted.',
                    }

                    transaction.commit()
                    return HttpResponse(json.dumps(response), 'application/json')

                else:
                    response = {
                        'status': 'forbidden',
                        'message': 'Your username and password did not authenticate successfully.',
                    }

                    transaction.rollback()
                    return HttpResponse(json.dumps(response), 'application/json')


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

def bulletinboard (request, slug):
    try:
        election = Election.objects.get(slug=slug)
    except Election.DoesNotExist:
        raise Http404
    else:
        finaldict = {}
        for race in election.races.all():

            ballots = race.sealedvotes.all()
            ballot_list = []

            for ballot in ballots:
                ballot_list.append((ballot.user_id,ballot.ballot,))

            finaldict[race.slug] = ballot_list

        output = json.dumps(finaldict)
        return render_to_response('referenda/bulletinboard.html',
                              locals(),
                              context_instance=RequestContext(request),
                              mimetype='application/json')
