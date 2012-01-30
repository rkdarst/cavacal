from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'cal.views.redirect_to_now'),
   (r'^now/$','cal.views.month',dict(year=None,month=None),'cal-month-future'),
    (r'^(?P<year>\d{4})/(?P<month>\d{1,2})/', 'cal.views.month'),
    (r'^set/(?P<shift_id>\d+)/(?P<rank_id>\d+)/', 'cal.views.setslot'),
    (r'^shift/(?P<shift_id>\d+)/(?P<rank_id>\d+)/', 'cal.views.shift'),
    (r'^search/', 'cal.views.search'),
    (r'^email/', 'cal.email.email'),
    (r'^log/(?P<shift_id>\d+)/(?P<rank_id>\d+)/', 'cal.views.log_shift'),
    (r'^log/(?P<shift_id>\d+)/', 'cal.views.log_shift'),
    (r'^log/', 'cal.views.log'),
    (r'^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/', 'cal.views.month_edit'),
    (r'^timing/(?P<year>\d{4})/(?P<month>\d{1,2})/', 'cal.views.month_timing'),
    (r'^raw/(?P<year>\d{4})/(?P<month>\d{1,2})/', 'cal.views.month_raw'),
    (r'^highlight/', 'cal.views.highlight'),
    (r'^time/histogram/', 'cal.views.time_histogram'),
    (r'^time/count/', 'cal.views.time_count'),
    (r'^time/', 'cal.views.time_person'),
#    (r'', 'cal.views.redirect_to_now'),

    (r'^motd/edit/$',             'cal.views.motd_edit'),
    (r'^motd/edit/(?P<id>\d+)/$', 'cal.views.motd_edit_i'),

    (r'^ical/$',                            'cal.export.ical'),
    (r'^ical/(?P<name>[^/]+)/$',            'cal.export.ical_search'),
    (r'^ical/person/(?P<name>[^/]+)/$',     'cal.export.ical_search'),
    (r'^ical/rank/(?P<rank_id>[^/]+)/$',    'cal.export.ical_rank'),
)

# This is imported by the urls_mobile module, since django can't
# import different names in one URL module.
urlpatterns_mobile = patterns('',
    (r'^(?P<shift_id>\d+)?/edit/$',    'cal.views.mobile_edit'),
    (r'^(?P<shift_id>\d+)?/$',         'cal.views.mobile'),
    (r'^edit/$',                       'cal.views.mobile_edit'),
    (r'^$',                            'cal.views.mobile'),

    (r'^upcoming/(?P<shift_id>\d+)/$', 'cal.views.mobile_upcoming'),
    (r'^upcoming/$',                   'cal.views.mobile_upcoming'),

    (r'^log/(?P<page>\d+)/$',          'cal.views.mobile_log'),
    (r'^log/$',                        'cal.views.mobile_log'),

    (r'^search/$',                     'cal.views.mobile_search'),
)
