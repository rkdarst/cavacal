from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'cavapeople.views.userpage'),
    (r'^change_username/$', 'cavapeople.views.change_username'),
    (r'^list_groups/$', 'cavapeople.views.list_groups'),
)
                       
