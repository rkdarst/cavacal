#!/usr/bin/env python

import wsgiref.handlers
import os, sys
import django.core.handlers.wsgi

sys.path.append("/srv/cava/")

os.environ['DJANGO_SETTINGS_MODULE'] = 'proj.settings'

wsgiref.handlers.CGIHandler().run(django.core.handlers.wsgi.WSGIHandler())
