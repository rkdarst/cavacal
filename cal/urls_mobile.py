from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    (r'^(?P<shift_id>\d+)?/edit/$',    'cal.views.mobile_edit'),
    (r'^(?P<shift_id>\d+)?/$',         'cal.views.mobile'),
    (r'^$',                            'cal.views.mobile'),

    (r'^upcoming/(?P<shift_id>\d+)/$', 'cal.views.mobile_upcoming'),
    (r'^upcoming/$',                   'cal.views.mobile_upcoming'),

    (r'^log/(?P<page>\d+)/$',          'cal.views.mobile_log'),
    (r'^log/$',                        'cal.views.mobile_log'),

    (r'^search/$',                     'cal.views.mobile_search'),
)
