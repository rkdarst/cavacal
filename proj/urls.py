from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^cavasite/', include('cavasite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^cal/', include('cal.urls')),
    (r'^user/', include('cavapeople.urls')),
    (r'^m/', include('cal.urls_mobile')),

#    (r'^m/(?P<shift_id>\d+)?/edit/$', 'cal.views.mobile_edit'),
#    (r'^m/(?P<shift_id>\d+)?/$', 'cal.views.mobile'),
#    (r'^m/$',                    'cal.views.mobile'),
#    (r'^m/upcoming/(?P<shift_id>\d+)/$', 'cal.views.mobile_upcoming'),
#    (r'^m/upcoming/$',                   'cal.views.mobile_upcoming'),
#    (r'^m/log/(?P<page>\d+)/$', 'cal.views.mobile_log'),
#    (r'^m/log/$',               'cal.views.mobile_log'),


    (r'^$', 'cal.views.redirect_to_now'),


    (r'^logout/', 'cavapeople.views.logout',
                  {'next_page': '/'}),
    (r'^about/', direct_to_template,
                  {'template': 'about.html'}, 'cal-about'),

#    (r'^accounts/', include('socialauth.urls')),
    (r'^openid/login/', 'django_openid_auth.views.login_begin',
                       {'template_name':'openid/login_custom.html'}),
    (r'^openid/', include('django_openid_auth.urls')),
    (r'^login/', 'django_openid_auth.views.login_begin',
                       {'template_name':'openid/login_custom.html'}),
)
