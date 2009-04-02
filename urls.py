from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_detail
from referenda.models import *

urlpatterns = patterns('',
    url(r'^$', 'referenda.views.home', name='referenda.home'),
    url(r'^license/$', direct_to_template, {'template': 'referenda/license.html'}, name='referenda.license'),
    url(r'^election/(?P<slug>[-_a-z0-9]+)/preview/$', 'referenda.views.preview', name='referenda.ballot_preview'),
    url(r'^election/(?P<slug>[-_a-z0-9]+)/$', object_detail, {'queryset': Election.objects.all(),'template_name': 'referenda/election_detail.html'}, name='referenda.election_detail'),
    url(r'^election/(?P<slug>[-_a-z0-9]+)/vote/$', 'referenda.views.voter_login', name='referenda.voter_login'),
    url(r'^election/(?P<slug>[-_a-z0-9]+)/submit/$', 'referenda.views.submit_ballot', name='referenda.submit_ballot'),
    url(r'^election/(?P<slug>[-_a-z0-9]+)/content/$', 'referenda.views.ballot_content', name='referenda.ballot_content'),
)
