#!/usr/bin/env python

import wsgiref.handlers
import os, sys
import django.core.handlers.wsgi

sys.path.append("/srv/cavacal/")
sys.path.append("/srv/cavacal/cavacal")

os.environ['DJANGO_SETTINGS_MODULE'] = 'cavacal.settings'

wsgiref.handlers.CGIHandler().run(django.core.handlers.wsgi.WSGIHandler())
