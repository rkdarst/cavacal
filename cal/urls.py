from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'cal.views.redirect_to_now'),
    (r'^(?P<year>\d{4})/(?P<month>\d{1,2})/', 'cal.views.month'),
    (r'^set/(?P<shift_id>\d+)/(?P<rank_id>\d+)/', 'cal.views.setslot'),
    (r'^search/', 'cal.views.search'),
    (r'^email/', 'cal.email.email'),
    (r'^log/', 'cal.views.log'),
    (r'^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/', 'cal.views.month_edit'),
    (r'^timing/(?P<year>\d{4})/(?P<month>\d{1,2})/', 'cal.views.month_timing'),
    (r'^raw/(?P<year>\d{4})/(?P<month>\d{1,2})/', 'cal.views.month_raw'),
    (r'^highlight/', 'cal.views.highlight'),
#    (r'', 'cal.views.redirect_to_now'),

    (r'^motd/edit/$',             'cal.views.motd_edit'),
    (r'^motd/edit/(?P<id>\d+)/$', 'cal.views.motd_edit_i'),

    (r'^ical/$',                            'cal.export.ical'),
    (r'^ical/(?P<name>[^/]+)/$',            'cal.export.ical_search'),
    (r'^ical/person/(?P<name>[^/]+)/$',     'cal.export.ical_search'),
    (r'^ical/rank/(?P<rank_id>[^/]+)/$',    'cal.export.ical_rank'),
)

mobilepatterns = patterns('',
    (r'^(?P<shift_id>\d+)?/edit/$', 'cal.views.mobile_edit'),
    (r'^(?P<shift_id>\d+)?/$', 'cal.views.mobile'),
    (r'^$',                    'cal.views.mobile'),
    (r'^upcoming/(?P<shift_id>\d+)/$', 'cal.views.mobile_upcoming'),
    (r'^upcoming/$',                   'cal.views.mobile_upcoming'),
    (r'^log/(?P<page>\d+)/$', 'cal.views.mobile_log'),
    (r'^log/$',               'cal.views.mobile_log'),
)
