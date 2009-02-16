from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_detail
from referenda.models import *

urlpatterns = patterns('',
    url(r'^$', 'referenda.views.home', name='referenda.home'),
    url(r'^license/$', direct_to_template, {'template': 'referenda/license.html'}, name='referenda.license'),

    # DELETE ME!
    url(r'^vote/$', direct_to_template, {'template': 'referenda/vote.html'}),

    url(r'^election/(?P<slug>[-_a-z0-9]+)/$', object_detail, {'queryset': Election.objects.all(),'template_name': 'referenda/election_detail.html'}, name='referenda.election_detail'),
    url(r'^election/(?P<slug>[-_a-z0-9]+)/vote/$', 'referenda.views.voter_login', name='referenda.voter_login'),

    # Components
    url(r'^election/(?P<election_slug>[-_a-z0-9]+)/components/race/(?P<race_slug>[-_a-z0-9]+)/$', 'referenda.views.vote_race', name='referenda.vote_race'),
    url(r'^election/(?P<election_slug>[-_a-z0-9]+)/components/frame/$', 'referenda.views.vote_frame', name='referenda.components.frame'),
    url(r'^election/(?P<election_slug>[-_a-z0-9]+)/components/setup/$', direct_to_template, {'template': 'referenda/components/setup.html',}, name='referenda.components.setup'),
)
