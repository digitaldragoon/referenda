from django.conf.urls.defaults import *
from django.views.generic.simple import *

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'referenda/base.html'}),
)
