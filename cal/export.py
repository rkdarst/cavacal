import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext, Template
from django.template.defaultfilters import pluralize
import django.template.loader
from django import forms

import cava.util
from models import Slot, Rank
import models
from cal.views import ranks, ifmodified_decorator

import pytz
import vobject

firstDate = datetime.date(2011,05,22)
firstShift = cava.util.Shift(date=firstDate, time='am')
calTimezone = pytz.timezone('US/Eastern')

class CalItem(object):
    def __init__(self, **kwargs):
        if 'start' in kwargs:
            kwargs['_start'] = kwargs['start']
            del kwargs['start']
        if 'end' in kwargs:
            kwargs['_end'] = kwargs['end']
            del kwargs['end']
        self.__dict__.update(kwargs)
    def start(self): return self._start
    def end(self):   return self._end
    def shift(self):
        """Make this seem like a 'slot' object."""
        return self

def makeIcal(slots, name=None):
    cal = vobject.iCalendar()
    for slot in slots:
        shift = slot.shift()
        if not slot.name or not slot.name.strip():
            continue
        event = cal.add('vevent')
        event.add('summary').value = slot.name
        event.add('uid').value = str(slot.shift_id)+'r'+str(slot.rank.rank_id)

        start = event.add('dtstart')
        start.value = shift.start().replace(tzinfo=calTimezone)

        end = event.add('dtend')
        end.value = shift.end().replace(tzinfo=calTimezone)

        others = Slot.objects.filter(shift_id=shift.shift_id).order_by("rank")
        others = "\n".join([ str(o.rank.rank_id )+' '+o.name
                             for o in others ])
        event.add('description').value = others


    cal.add('X-PUBLISHED-TTL').value = "PT1H"
    cal.add('method').value = 'PUBLISH'  # IE/Outlook needs this (see http://blog.thescoop.org/archives/2007/07/31/django-ical-and-vobject/)

    if name:
        cal.add('x-wr-calname').value = name
        cal.add('x-wr-caldesc').value = name

    return cal

def HttpResponseIcal(*args, **kwargs):
    """Convenience function to create iCal and return HTTPResponse of it."""
    cal = makeIcal(*args, **kwargs)
    body = cal.serialize()
    response = HttpResponse(body, mimetype="text/plain")
    if 'name' in kwargs:
        response["Filename"] = kwargs['name']+'.ics'
        #response['Content-Disposition'] = 'attachment; filename=%s.ics'%kwargs['name'] # IE reportedly needs this...
    #response["Cache-Control"] = "max-age=7200, private, must-revalidate"
    return response

class SearchForm(forms.Form):
    q = forms.CharField(label="Your calendar name")
#    regex   = forms.BooleanField(required=False, initial=False,
#                                 widget=forms.HiddenInput())
def ical(request):
    ranklist = ranks
    regex = False
    if 'regex' in request.REQUEST:
        regex = True

    form = SearchForm(request.GET)
    if form.is_valid():
        matches = models.slot_search(pattern=form.cleaned_data['q'],
                    shift_id__gt=cava.util.get_current_shift().shift_id,
                    regex=regex)[:25]
    else:
        form = SearchForm()
    t = django.template.loader.get_template("ical.html")
    c = RequestContext(request, locals())
    body = t.render(c)
    return HttpResponse(body)

@ifmodified_decorator
def ical_search(request, name):
    """Return the ical based on a search for 'name'"""
    if 'regex' in request.REQUEST:
        regex = True
    else:
        regex = False
    matches = models.slot_search(name,
                                 shift_id__gt=firstShift.shift_id,
                                 regex=regex)
    matches.order_by('-shift_id')
    return HttpResponseIcal(matches, name='CAVA - %s'%name)

@ifmodified_decorator
def ical_rank(request, rank_id):
    """Return an ical for a certain rank"""
    rank = Rank.objects.get(rank_id=int(rank_id))

    matches = Slot.objects.filter(rank=rank,
                                  shift_id__gt=firstShift.shift_id)
    matches.order_by('-shift_id')
    return HttpResponseIcal(matches, name='CAVA - %ss'%rank.rank)
