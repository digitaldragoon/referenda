from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_detail
from referenda.models import *

urlpatterns = patterns('',
    url(r'^$', 'referenda.views.home', name='referenda.home'),
    url(r'^about/$', direct_to_template, {'template': 'referenda/about.html'}, name='referenda.about'),
    url(r'^license/$', direct_to_template, {'template': 'referenda/license.html'}, name='referenda.license'),
    url(r'^election/(?P<election_slug>[-_a-z0-9]+)/preview/$', 'referenda.views.preview', name='referenda.ballot_preview'),
    url(r'^election/(?P<slug>[-_a-z0-9]+)/$', 'referenda.views.election_detail', name='referenda.election_detail'),
    url(r'^election/(?P<slug>[-_a-z0-9]+)/bulletinboard.json$', 'referenda.views.bulletinboard', name='referenda.bulletinboard'),
    url(r'^election/(?P<election_slug>[-_a-z0-9]+)/trustee/$', 'referenda.views.trustee', name='referenda.trustee'),
    url(r'^election/(?P<election_slug>[-_a-z0-9]+)/trustee/submit/$', 'referenda.views.submit_tally', name='referenda.submit_tally'),
    url(r'^election/(?P<election_slug>[-_a-z0-9]+)/vote/$', 'referenda.views.booth', name='referenda.booth'),
    url(r'^election/(?P<election_slug>[-_a-z0-9]+)/vote/submit/$', 'referenda.views.submit_ballot', name='referenda.submit_ballot'),
    url(r'^election/(?P<election_slug>[-_a-z0-9]+)/(?P<type>vote|trustee)/templates/(?P<template_name>.*)/$', 'referenda.views.javascript_template', name='referenda.javascript_template'),
)
