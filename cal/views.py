# Create your views here.

import collections
import datetime
import textwrap
import os
import re

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import Context, RequestContext, Template
import django.template
import django.core.mail as dj_mail
#from django.core.exceptions import DoesNotExist
from django.core.urlresolvers import reverse, resolve
from django.shortcuts import redirect
from django import forms
from django.contrib.auth.decorators import permission_required
from django.utils.html import escape
import django.views.decorators.http

#from models import Rank, Slot
from models import Rank, Slot, Schedule, LogSlot, Motd
import models
schedule = Schedule()
ranks = Rank.objects.order_by('rank_id')

#import sys ; sys.path.append('/home/richard/rkd/org/cava/')
import cava.util
from cava.util import Shift

def coverage_re_replace(match):
    return '<span class="coverage">%s</span>'%match.group(0)
coverage_re = re.compile('\?+|coverage|help|[\w ]+\*',re.I)
time_re = re.compile('(([0-9:])|((?<!<)/))+')
#hide_re = re.compile(r'\b(richard|harstrick)\b', re.I)
def highlight_names(name, highlight=None, view=None):
    name = coverage_re.sub(coverage_re_replace, name)
    if highlight:
        name = highlight.sub(lambda m: '<b>%s</b>'%m.group(0), name)
    #name = hide_re.sub(lambda m: '<i>hidden</i>', name)
    if view != "mobile":
        pass
        name = time_re.sub(lambda m: '<font size="-1">%s</font>'%m.group(0),
                           name)
        #name = time_re.sub(lambda m:'<font color="gray">%s</font>'%m.group(0),
        #                   name)
    name = name.replace('//', '/&#8203;/')
    return name


# These two implement conditional content processing (returning 304 if
# nothing is new in the log).  See
# https://docs.djangoproject.com/en/dev//topics/conditional-view-processing/
def etag(*args, **kwargs):
    return models.last_modified().strftime('%s')
def lastmodified(*args, **kwargs):
    return models.last_modified()
ifmodified_decorator = django.views.decorators.http.condition(
    etag_func=etag,
    last_modified_func=lastmodified)
# This disables the conditional processing (uncomment to use)
#ifmodified_decorator = lambda x: x


def redirect_to_now_month(request, today=None, rank_id=None):
    if today is None:
        today = datetime.date.today()
    if today.day > 4:
        day = today.day - 4
        bookmark = '#%02d'%day
    else:
        bookmark = ""
    querylist = [ ]
    if rank_id is not None:
        querylist.append('rank_id=%d'%rank_id)
    q = request.META.get('QUERY_STRING')
    if q:
        querylist.append(q)
    if len(querylist) > 0:
        query = '?'+"&".join(querylist)
    else:
        query = ""
    kwargs = dict(year=today.year, month="%02d"%today.month)
    return HttpResponseRedirect(
        reverse(month, kwargs=kwargs)+query+bookmark)

def redirect_to_now_future(request, today=None, rank_id=None):
    querylist = [ ]
    if rank_id is not None:
        querylist.append('rank_id=%d'%rank_id)
    q = request.META.get('QUERY_STRING')
    if q:
        querylist.append(q)
    if len(querylist) > 0:
        query = '?'+"&".join(querylist)
    else:
        query = ""
    return HttpResponseRedirect(reverse('cal-month-future')+query)
redirect_to_now = redirect_to_now_future

class SetSlotForm(forms.Form):
    name = forms.CharField(max_length=256, required=False)
    next = forms.CharField(widget=forms.HiddenInput(), required=False)

@permission_required('cal.can_edit_calendar')
def setslot(request, shift_id, rank_id):
    REQUEST = request.REQUEST

    shift_id = int(shift_id)
    rank_id  = int(rank_id)

    if request.method == 'POST':
        form = SetSlotForm(request.POST)
        if form.is_valid():
            schedule.setslot((shift_id, rank_id),
                             form.cleaned_data['name'],
                             user=request.user
                             )
            if form.cleaned_data['next']:
                next = form.cleaned_data['next']
                #try:
                #    nextview = resolve(next)
                #except Http404:
                #    nextview = None
                #if nextview:
                #    if nextview.func == month and 'rank_id' not in next:
                #        next += '#%02d'%shift_id.date.day
                #else:
                #    next += '#'+next
                #if 'rank_id' not in next:
                #    return redirect_to_now(request, today=Shift(shift_id).date)
                return HttpResponseRedirect(next)

            return redirect_to_now(request, today=Shift(shift_id).date)
#        print form.name_of_field.errors
    else:
        form = SetSlotForm(initial={'name':schedule[shift_id, rank_id],
                               'next': request.META.get('HTTP_REFERER')})

    t = django.template.loader.get_template("cava/setslot.html")
    body = t.render(RequestContext(request, locals()))
    return HttpResponse(body)


def day_cell(date, rank, can_edit=False, schedule=schedule, highlight=None,
             tooltips=False, limit=None):
    cell = [ ]
    for time in 'am', 'pm':
        shift = cava.util.Shift(date=date, time=time)
        timerepl = time.upper()

        # Needs to be fixed for the case that a slot doesn't exist already.
        name = schedule[shift.shift_id, rank]
        if limit:
            if not limit.search(name):
                name = ''
        if name:
            name = escape(name)
            name = highlight_names(name, highlight=highlight)

        link = reverse(shift_info,
                       kwargs=dict(shift_id=int(shift), rank_id=rank.rank_id))

        #if shift.date < datetime.date.today():
        #    can_edit = False

        # # Do authentication / deciding if we should link here.
        # if not can_edit:
        #     slot = '%(time)s: %(name)s'
        #     #slot = '{{time|upper}}: {{name}}'
        # elif not name.strip():
        #     # rel="shadowbox"
        #     slot = '<a href="%(link)s" class="elnk">%(time)s:</a>'
        #     #slot = '<a href="{{link}}">{{time|upper}}:</a>'
        # else:
        #     #slot = '%(time)s: <a href="%(link)s">%(name)s</a>'
        #     slot = '<a href="%(link)s" class="elnk">%(time)s:</a> %(name)s'
        #     #slot = '{{time|upper}}: <a href="{{link}}">{{name}}</a>'

        slot = '<a href="%(link)s" class="elnk">%(time)s:</a> %(name)s'


        # Tool tip for all shifts
        if tooltips:
            tooltip = [ ]
            for _rank in ranks:
                s = schedule[shift.shift_id, _rank]
                if not s or not s.strip():
                    continue
                tooltip.append("%s: %s"%(_rank.rank, s))
            if tooltip:
                timerepl = '<span title="%s">%s</span>'%(
                    ', &#10;'.join(tooltip), timerepl)

        slot = slot%{'time':timerepl, 'link':link, 'name':name}
        #Template(slot).render(Context(locals()))
        cell.append(slot)
    cell = '<br>'.join(cell)
    return cell


def shift(request, shift_id, rank_id):
    REQUEST = request.REQUEST

    shift_id = int(shift_id)
    shift = Shift(shift_id)
    rank_id  = int(rank_id)
    rank = Rank.objects.get(rank_id=rank_id)
    try:
        slot = Slot.objects.get(shift_id=shift_id, rank=rank)
        parsed_shift = cava.util.parseslot(shift, slot.name)
    except Slot.DoesNotExist:
        slot = None

    # Edit-related things
    can_edit = False
    if request.user.has_perm('cal.can_edit_calendar'):
        can_edit = True
        if request.method == 'POST':
            form = SetSlotForm(request.POST)
            if form.is_valid():
                schedule.setslot((shift_id, rank_id),
                                 form.cleaned_data['name'],
                                 user=request.user
                                 )
                if form.cleaned_data['next']:
                    next = form.cleaned_data['next']
                    return HttpResponseRedirect(next)

                return redirect_to_now(request, today=Shift(shift_id).date)
        else:
            form = SetSlotForm(initial={'name':schedule[shift_id, rank_id],
                                   'next': request.META.get('HTTP_REFERER')})


    log = LogSlot.objects.filter(
        shift_id=shift_id, rank=rank_id).order_by('mtime').reverse()

    t = django.template.loader.get_template("cava/shift.html")
    body = t.render(RequestContext(request, locals()))
    return HttpResponse(body)
shift_info = shift


#@permission_required('cal.can_view_calendar')
#@ifmodified_decorator
def month(request, year, month):
    if year is not None and month is not None:
        year = int(year)
        month = int(month)
        date = datetime.date(year, month, 1)
        stopDate = cava.util.increment_month(date)
        stopDate += datetime.timedelta(days=5)
        if 'rank_id' in request.REQUEST:
            stopDate += datetime.timedelta(days=2)
        # Create a cache
        first_shift_id = Shift(date=date,time='am').shift_id
        schedule = Schedule(cache=(first_shift_id, first_shift_id+2*31+10))
        title = date.strftime('CAVA: %Y %B')
    else:
        if 'start' in request.REQUEST:
            date = datetime.datetime.strptime(request.REQUEST['start'],
                                              '%Y-%m-%d').date()
        else:
            date = datetime.date.today() - datetime.timedelta(days=3)
        if 'end' in request.REQUEST:
            stopDate = datetime.datetime.strptime(request.REQUEST['end'],
                                                  '%Y-%m-%d').date()
            _stopDate = datetime.datetime(stopDate.year,
                                      stopDate.month,
                                      stopDate.day)
            end_slot = cava.util.get_current_shift(now=_stopDate)
        else:
            end_slot = Slot.objects.order_by('-shift_id')[0]
            stopDate = end_slot.shift().date
        # Create a cache
        first_shift_id = Shift(date=date,time='am').shift_id
        schedule = Schedule(cache=(first_shift_id, end_slot.shift_id))
        title = 'CAVA: Future'
    calendardate = date
    ranktitle = ""
    rows = [ ]
    today = datetime.date.today()
    # We don't want to import this here, but due to recursive imports,
    # middleware doesn't load before views loads, causing problems,
    # and this is the easiest way around it
    import middleware

    can_edit = False
    if request.user.has_perm("cal.can_edit_calendar"):
        can_edit = True

    # Open question: I am not re.escape'ing things here to allow RE
    # features to be used.  How bad of security problems does this
    # make?
    highlight = None
    if 'highlight' in request.REQUEST:
        highlight = request.REQUEST.get('highlight')
    elif 'highlight-name' in request.COOKIES:
        highlight = request.COOKIES['highlight-name']
    if highlight:
        highlight = re.compile(highlight, re.I)
    tooltips = False
    limit = None
    if 'limit' in request.REQUEST:
        limit = re.compile(request.REQUEST['limit'], re.I)
        tooltips = True
        if not highlight:
            highlight = re.compile(request.REQUEST['limit'], re.I)

    if request.REQUEST.get('rank_id', None):
        # Calendar view for one rank
        # Start on Monday
        table = [ ]
        date -= datetime.timedelta(days=date.weekday())

        rank_id = int(request.REQUEST['rank_id'])
        rank = Rank.objects.get(rank_id=rank_id)
        title += ', %s'%rank.rank

        for nweek in range(20): # max number of weeks to possibly do
            week_row = [ ]
            for nweekday in range(7):
                next_month = cava.util.increment_month(date, 1)
                if month is None and nweekday == 0 and \
                       (next_month-date) < datetime.timedelta(7):
                    month_bar = middleware.NavBarMiddleware.month_bar.im_func(
                        None, request, view_month,
                        kwargs=dict(month=next_month.month,
                                    year=next_month.year))
                    contents = ('<td colspan="%s"><center>'
                                '%s'
                                '</center></td>')%(
                        7, month_bar)
                    table.append(dict(contents=contents))

                datestr = date.strftime("<center>%d</center>")
                if date.month == month:
                    datestr = '<b>%s</b>'%datestr

                classes = [ ]
                if date == today:
                    classes.append("today")
                if month is not None and date.month != month:
                    classes.append("notthismonth")
                elif date.weekday() in (5,6):
                    classes.append("weekend")
                if classes:
                    style = ' class="%s"'%(' '.join(classes))
                else:
                    style = ''

                cell  = day_cell(date, rank, can_edit=can_edit,
                                 schedule=schedule,
                                 highlight=highlight,
                                 tooltips=True,
                                 limit=limit)
                cell = '%s%s'%(datestr, cell)
                cell = '<td%s>%s</td>'%(style, cell)
                week_row.append(cell)
                date += datetime.timedelta(days=1)
            table.append(week_row)
            # Break condition for doing a single month:
            if date > stopDate:
                break

        template = django.template.loader.get_template("cava/calendar_month.html")

    else:
        # If we are within 3 days of next month, show it anyway:
        if 0 < (date - today).days < 5:
            date = today

        # All ranks in a vertical table
        table_header = ["<b>%s</b>"%(rank.rank) for rank in ranks ]
        table_header = ["<td>%s</td>"%h for h in table_header]
        #table_header = ' '.join(table_header)

        table = [ ]
        while True:
            if date > stopDate:
                break

            if month is None and date.day == 1:
                month_bar = middleware.NavBarMiddleware.month_bar.im_func(
                    None, request, view_month,
                    kwargs=dict(month=date.month, year=date.year))
                contents = ('<td colspan="%s"><center>'
                            '%s'
                            '</center></td>')%(
                    len(ranks)+1, month_bar)
                table.append(dict(contents=contents))

            row = {'row':[ ]}
            row['day'] = "%02d"%date.day
            row['month'] = date.strftime("%b")
            row['weekday'] = date.strftime("%a")
            row['today'] = False
            if date.month != month:  row['moreclasses'] = " notthismonth"
            else:                    row['moreclasses'] = ''
            for rank in ranks:

                classes = [ ]
                if date == today:
                    classes.append("today")
                if month is not None and date.month != month:
                    classes.append("notthismonth")
                elif date.weekday() in (5,6):
                    classes.append("weekend")
                if classes:
                    style = ' class="%s"'%(' '.join(classes))
                else:
                    style = ''

                cell = day_cell(date, rank, can_edit=can_edit,
                                schedule=schedule,
                                highlight=highlight,
                                limit=limit,
                                tooltips=tooltips)
                cell = '<td%s>%s</td>'%(style, cell)
                row['row'].append(cell)
            table.append(row)

            if date.weekday() in (4,6):
                table.append({'empty':True }) # ['<tr cellpadding=5><td></td></tr>']
            date += datetime.timedelta(days=1)

        template = django.template.loader.get_template("cava/calendar.html")

    body = template.render(RequestContext(request, locals()))
    return HttpResponse(body)
view_month = month

def month_timing(*args, **kwargs):
    for i in range(1000):
        month(*args, **kwargs)
    return month(*args, **kwargs)


def calendar_generator(year, month, cell_callback):
    table = [ ]
    date = datetime.date(year, month, 1)
    today = datetime.date.today()
    date -= datetime.timedelta(days=date.weekday()) # Go to start of week

    for i in range(8): # max number of weeks to possibly do
        week_row = [ ]
        for i in range(7):
            datestr = date.strftime("<center>%d</center>")
            if date.month == month:
                datestr = '<b>%s</b>'%datestr
            #cell  = day_cell(date, rank, can_edit=can_edit)
            cell = cell_callback(date)
            cell = '%s%s'%(datestr, cell)
            style = ''
            if date == today:
                style += ' class="today"'
            if date.month != month:
                style += ' class="notthismonth"'
            elif date.weekday() in (5,6):
                style += ' class="weekend"'
            cell = '<td%s>%s</td>'%(style, cell)
            week_row.append(cell)
            date += datetime.timedelta(days=1)
        table.append(week_row)
        if date.month != month and date.day > 7:
            break
    return table


#@permission_required('cal.can_edit_calendar')
def month_edit(request, year, month):
    year = int(year)
    month = int(month)

    date = datetime.date(year, month, 1)
    today = datetime.date.today()

    can_edit = False
    if request.user.has_perm("cal.can_edit_calendar"):
        can_edit = True

    if 'rank_id' in request.REQUEST:
        rank_id = int(request.REQUEST['rank_id'])
    else:
        rank_id = 1
    rank = Rank.objects.get(rank_id=rank_id)

    shifts = [ ]
    def cell_callback(date):
        am_shift = Shift(date=date, time='am')
        pm_shift = Shift(date=date, time='pm')
        am_name = 'f'+str(am_shift.shift_id)+'am'
        pm_name = 'f'+str(pm_shift.shift_id)+'pm'
        shifts.append((am_name, am_shift))
        shifts.append((pm_name, pm_shift))
        cell = '{{form.%s}}<br>{{form.%s}}<br>'%(am_name, pm_name)
        return cell
    table = calendar_generator(year, month, cell_callback)


    formdict = { }
    for name, shift in shifts:
        formdict[name] = forms.CharField(max_length=256,
                                         initial=schedule[shift, rank],
                                         required=False)

    MonthEditForm = type('MonthEditForm', (forms.Form, ), formdict)


    if request.method == "POST":
        form = MonthEditForm(request.POST)
        if form.is_valid():
            for name, shift in shifts:
                new = form.clean()[name]
                initial = form.fields[name].initial
                if new == initial:
                    continue
                schedule.setslot((shift, rank),
                                 new,
                                 request.user)
#        from fitz import interactnow
            return redirect_to_now(request,
                                   today=date,
                                   rank_id=rank_id)
    else:
        form = MonthEditForm()


    template = django.template.loader.get_template("cava/calendar_month_edit.html")

    body = template.render(RequestContext(request, locals()))
    t = Template(body)
    body = t.render(RequestContext(request, locals()))
    return HttpResponse(body)

class SearchForm(forms.Form):
    q = forms.CharField(max_length=256, required=False)
    regex = forms.BooleanField(required=False)

def search(request, searchstr=None):
    if 'q' in request.REQUEST:
        searchstr = request.REQUEST['q']
    elif searchstr is not None and searchstr.strip():
        stearchstr = searchstr
    else:
        searchstr = ''
    regex = False
    if request.REQUEST.get('regex', False):
        regex = True

    if searchstr:
        if regex:
            matches = Slot.objects.filter(name__iregex=searchstr)
        else:
            matches = Slot.objects.filter(name__icontains=searchstr)
        matches.order_by('-shift_id')
        #matches.reverse()
        # FIXME why do I have to order things again, why does SQL not work?
        matches = list(matches)
        matches.sort(key=lambda x: x.shift_id, reverse=True)

    template = django.template.loader.get_template("cava/search.html")
    body = template.render(RequestContext(request, locals()))
    return HttpResponse(body)

def log(request):
    """Changelog for all changes for the last 168 hours.
    """

    slots = LogSlot.objects.filter(
        mtime__gte=datetime.datetime.now()-datetime.timedelta(hours=168)
        ).order_by('mtime').reverse()

    t = django.template.loader.get_template("cava/log.html")
    body = t.render(RequestContext(request, locals()))
    return HttpResponse(body)

def log_shift(request, shift_id, rank_id=None):
    """Changelog for just one shift, optionally for only one rank.
    """
    shift_id = int(shift_id)
    shift = Shift(shift_id=shift_id)
    # Optional filtering by rank
    filterargs = { }
    ranktitle = ""
    if rank_id is not None:
        rank_id = int(rank_id)
        filterargs['rank'] = Rank.objects.get(rank_id=rank_id)
        ranktitle = filterargs['rank'].rank

    slots = LogSlot.objects.filter(
        shift_id=shift_id,
        **filterargs
        ).order_by('mtime').reverse()
    t = django.template.loader.get_template("cava/log_shift.html")
    body = t.render(RequestContext(request, locals()))
    return HttpResponse(body)


def month_raw(request, year, month):
    lines = [ ]
    year = int(year)
    month = int(month)
    shift = Shift(date=datetime.date(year,month, 1), time='am')
    body = [ ]
    while shift.date.month == month:
        for rank in ranks:
            body.append('%s\t%s\t%s\t%s\t%s'%(
                shift.shift_id, shift.date.strftime("%Y-%m-%d"),
                shift.time, rank.rank_id, schedule[shift, rank]))
        shift = shift.next

    return HttpResponse("\n".join(body), content_type='text/plain')


def shift_data(shift):
    data = { }
    data['shifttitle'] = \
                   shift.date.strftime("%a, %b %d, %Y, %%s")%shift.time.upper()
    data['prevlink'] = reverse(mobile, kwargs={'shift_id':int(shift.previous)})
    data['nextlink'] = reverse(mobile, kwargs={'shift_id':int(shift.next)})

    data['names'] = names = [ ]
    for rank in ranks:
        name = schedule[shift, rank]
        name = escape(name)
        name = highlight_names(name)
        names.append(name)
    return data

def mobile(request, shift_id=None):
    if shift_id is None:
        shift = cava.util.get_current_shift(
                    now=datetime.datetime.now()+datetime.timedelta(hours=1))
        home = True
    else:
        shift_id = int(shift_id)
        shift = Shift(shift_id)
        home = False

    data = shift_data(shift)
    title = data['shifttitle']
    data.update(locals())

    t = django.template.loader.get_template("cava/mobile.html")
    body = t.render(RequestContext(request, data))
    return HttpResponse(body)


#class ShiftEditForm(forms.Form):
#    pass
sef_d = { }
sef_mapping = { }
for rank in ranks:
    f = forms.CharField(max_length=256, required=False,
                        label=rank.rank)
    shortRankName = re.subn('[^a-zA-Z]+', '', rank.rank)[0].lower()
    sef_d[shortRankName] = f
    #rank.rank_id
    sef_mapping[shortRankName] = rank
ShiftEditForm = type("ShiftEditForm", (forms.Form, ), sef_d)
del rank, f, shortRankName

def mobile_edit(request, shift_id=None):
    if shift_id is None:
        shift = cava.util.get_current_shift(
                    now=datetime.datetime.now()+datetime.timedelta(hours=1))
        shift_id = int(shift)
        home = True
    else:
        shift_id = int(shift_id)
        shift = Shift(shift_id)
        home = False
    title = shifttitle = "Editing %s %s"%(shift.date.strftime("%Y, %b %d"),
                                          shift.time)

    if request.method == "POST":
        form = ShiftEditForm(request.POST)
        if form.is_valid():
            for fieldname, rank in sef_mapping.items():
                new = form.clean()[fieldname]
                if new == schedule[shift_id, rank]:
                    continue
                schedule.setslot((shift, rank),
                                 new,
                                 #user=request.user,
                                 user="mobile",
                                 )
            return HttpResponseRedirect(reverse(mobile,
                                                kwargs={'shift_id':shift_id}))
    else:
        initial = dict((fieldname, schedule[shift_id, rnk])
                       for (fieldname, rnk) in sef_mapping.items())
        form = ShiftEditForm(initial=initial)

    t = django.template.loader.get_template("cava/mobile_edit.html")
    body = t.render(RequestContext(request, locals()))
    return HttpResponse(body)


def mobile_upcoming(request, shift_id=None, numShifts=8):
    """Page listing the upcoming numShifts shifts."""
    if shift_id is None:
        shift = cava.util.get_current_shift(
                    now=datetime.datetime.now()-datetime.timedelta(hours=1))
        home = True
    else:
        shift_id = int(shift_id)
        shift = Shift(shift_id)
        home = False

    shifts = [ ]
    thisshift = shift
    for i in range(numShifts):
        shifts.append(shift_data(thisshift))
        thisshift = thisshift.next
    nextlink = reverse(mobile_upcoming, kwargs={'shift_id':int(shift)+numShifts})
    prevlink = reverse(mobile_upcoming, kwargs={'shift_id':int(shift)-numShifts})

    t = django.template.loader.get_template("cava/mobile_upcoming.html")
    body = t.render(RequestContext(request, locals()))
    return HttpResponse(body)

def mobile_log(request, page=None, numPerPage=5):
    if page is None:  page = 1
    page = int(page)
    if page <= 0:     page = 1
    nextlink = reverse(mobile_log, kwargs=dict(page=page+1))

    if   page == 1:  pass #prevlink = None
    elif page == 2:  prevlink = reverse(mobile_log)
    else:            prevlink = reverse(mobile_log, kwargs=dict(page=page-1))

    currentShift = cava.util.get_current_shift()
    #slots = LogSlot.objects.filter(
    #    mtime__gte=datetime.datetime.now()-datetime.timedelta(hours=168)
    #    ).order_by('-id')
    slots = LogSlot.objects.filter(
        mtime__gte=datetime.datetime.now()-datetime.timedelta(hours=72),
        shift_id__gte=currentShift.shift_id,
        shift_id__lte=currentShift.shift_id+5,
        ).order_by('-mtime')

    bodytitle = "Recent changes"
    if page > 1:
        bodytitle += " (page %d)"%page

    from django.core.paginator import Paginator
    p = Paginator(slots, numPerPage)
    currentpage = p.page(page)

    t = django.template.loader.get_template("cava/mobile_log.html")
    body = t.render(RequestContext(request, locals()))
    return HttpResponse(body)

class MobileSearchForm(forms.Form):
    q = forms.CharField(label="")
def mobile_search(request):
    initial = { }
    q = None
    if 'q' in request.REQUEST:
        q = request.REQUEST['q']
    elif 'search-name' in request.COOKIES:
        q = request.COOKIES['q']
    if q:
        initial['q'] = q
    form = MobileSearchForm(initial=initial)

    if q:
        matches = Slot.objects.filter(name__icontains=q)
        matches.order_by('shift_id')
        matches = list(matches)
        matches.sort(key=lambda x: x.shift_id, reverse=True)

    t = django.template.loader.get_template("cava/mobile_search.html")
    c = RequestContext(request, locals())
    body = t.render(c)
    return HttpResponse(body)


def motd_edit(request, id=None):
    if request.method == "POST" and request.POST.get('add', False):
        Motd().save()

        return redirect(reverse(motd_edit))
    motdList = Motd.objects.order_by("-id")
    c = RequestContext(request, locals())
    t = django.template.loader.get_template("cava/motd_edit.html")
    return HttpResponse(t.render(c))

class MotdForm(forms.ModelForm):
    class Meta:
        model = Motd
    def clean_message(self):
        return self.cleaned_data['message'].strip()

def motd_edit_i(request, id=None):
    id = int(id)
    if request.method == "POST":
        if request.POST['submit'] == "Delete":
            Motd.objects.get(id=id).delete()
            return redirect(reverse(motd_edit))
        form = MotdForm(request.POST, instance=Motd.objects.get(id=id))
        if form.is_valid():
            form.save()
            #print request.POST['submit']
            if request.POST['submit'] == "Save and return":
                #print True
                return redirect(reverse(motd_edit))
            return redirect(reverse(motd_edit_i, kwargs=dict(id=id)))
    else:
        form = MotdForm(instance=Motd.objects.get(id=id))

    c = RequestContext(request, locals())
    t = django.template.loader.get_template("cava/motd_edit_i.html")
    return HttpResponse(t.render(c))




class HighlightForm(forms.Form):
    name = forms.CharField()
    referrer = forms.CharField(widget=forms.HiddenInput,
                               required=False)
def highlight(request):
    if request.method == "POST":
        form = HighlightForm(request.POST)
        if form.is_valid(): # pretty much a null-up here, no real validation
            if form.cleaned_data['referrer']:
                redirectTo = form.cleaned_data['referrer']
            else:
                redirectTo = reverse(redirect_to_now)
            response = HttpResponseRedirect(redirectTo)
            response.set_cookie("highlight-name",form.cleaned_data['name'],
                    expires=datetime.date.today()+datetime.timedelta(days=60))
            return response
    else:
        form = HighlightForm(initial=dict(
            referrer=request.META.get('HTTP_REFERER', ''),
            name=request.COOKIES.get('highlight-name', '')))

    t = django.template.loader.get_template("cava/highlight.html")
    c = RequestContext(request, locals())
    body = t.render(c)
    return HttpResponse(body)



class TimePersonForm(forms.Form):
    q = forms.CharField(max_length=256, label="Name", required=1,
                        error_messages={'required':
                                        'You must enter a name.'})
    rank = forms.ModelChoiceField(Rank.objects.all(), required=False)
    firstdate = forms.DateField(label="First date (YYYY-MM-DD)",required=False)
    lastdate  = forms.DateField(label="Last date (YYYY-MM-DD)", required=False)
    weekend  = forms.BooleanField(label="Limit to weekends", required=False)
    regex  = forms.BooleanField(label="Regular expression search?",
                                required=False,
                                widget=forms.HiddenInput())
class TimeCountForm(forms.Form):
    rank = forms.ModelChoiceField(Rank.objects.all(), required=False)
    firstdate = forms.DateField(label="First date (YYYY-MM-DD)",required=False)
    lastdate  = forms.DateField(label="Last date (YYYY-MM-DD)", required=False)
    weekend  = forms.BooleanField(label="Limit to weekends", required=False)
    regex  = forms.BooleanField(label="Regular expression search?",
                                required=False,
                                widget=forms.HiddenInput())
def get_time_slots(regex=False, **kwargs):
    """Get time slots
    """

    searchargs = { }
    if 'q' in kwargs:
        use_regex = regex
        if use_regex:
            searchargs['name__iregex'] = kwargs['q']
        else:
            searchargs['name__icontains'] = kwargs['q']

    firstdate = None
    lastdate = None
    if kwargs['firstdate']:
        firstdate = kwargs['firstdate']
        searchargs['shift_id__gte'] = Shift(date=firstdate, time='am')
    if kwargs['lastdate']:
        lastdate = kwargs['lastdate']
        searchargs['shift_id__lte'] = Shift(date=lastdate, time='pm')
    if kwargs.get('rank', None):
        searchargs['rank'] = kwargs['rank']

    matches = Slot.objects.filter(**searchargs)
    matches.order_by('-shift_id')
    matches = list(matches)
    if kwargs.get('weekend', False):
        matches = [ m for m in matches if m.shift().is_weekend() ]
    matches.sort(key=lambda x: x.shift_id, reverse=True)
    return matches

def time_person(request, q=None):
    form = TimePersonForm(request.GET)
    if not form.is_valid():
        pass
    else:
        q = form.cleaned_data['q']
        use_regex = form.cleaned_data.get('regex', False)
        if use_regex:
            regex_pattern = re.compile(q, re.I)
        matches = get_time_slots(**form.cleaned_data)

        # Generate all the rows.
        rows = [ ]
        cumulative = datetime.timedelta()
        for slot in matches:
            intervals = cava.util.parseslot(slot.shift(), slot.name)
            for name, start, end in intervals:
                if (   (not use_regex and q.lower() in name.lower())
                    or (    use_regex and regex_pattern.search(name) )):
                    #if start is None or end is None:
                    #    continue
                    dt = end-start
                    cumulative += dt
                    seconds = cumulative.days*24*3600 + cumulative.seconds
                    hours = seconds / 3600.
                    row = dict(slot=slot,
                               #shift=slot.shift().text(),
                               #slotname=slot.name,
                               name=name,
                               start=start,
                               end=end,
                               dt=dt,
                               cum=cumulative,
                               cumhours=hours,
                               )
                    rows.append(row)

    template = django.template.loader.get_template("cava/time_person.html")
    body = template.render(RequestContext(request, locals()))
    return HttpResponse(body)

def time_count(request):
    form = TimeCountForm(request.GET)
    form.is_valid()

    personqueryargs = request.GET.copy()
    for key in request.GET:
        if key not in ('regex', 'rank', 'firstdate', 'lastdate'):
            del personqueryargs[key]

    matches = get_time_slots(**form.cleaned_data)

    # Generate all the rows.
    count = collections.defaultdict(lambda: [datetime.timedelta(),
                                             datetime.timedelta()])
    cumulative = datetime.timedelta()
    ignoreCharRe = re.compile(r'[*?]+')
    for slot in matches:
        intervals = cava.util.parseslot(slot.shift(), slot.name)
        for name, start, end in intervals:
                #if start is None or end is None:
                #    continue
                dt = end-start
                name = name.lower()
                name = ignoreCharRe.sub('', name)
                count[name][0] += dt
                if slot.shift().is_weekend():
                    count[name][1] += dt

    rows = [ ]
    for name, (dt, dt_weekend) in sorted(count.iteritems(),
                                         reverse=True, key=lambda x:x[1][0]):
        personqueryargs['q'] = name
        rows.append(dict(name=name,
                         dt=dt,
                         hours=(dt.days*24)+dt.seconds/3600.,
                         hours_weekend=(dt_weekend.days*24)+\
                                        dt_weekend.seconds/3600.,
                         queryargs=personqueryargs.urlencode(),
                         ))

    template = django.template.loader.get_template("cava/time_count.html")
    body = template.render(RequestContext(request, locals()))
    return HttpResponse(body)
def _time_since_weekstart(d):
    weekstart = d - datetime.timedelta(days=d.weekday())
    td = (d - datetime.datetime(weekstart.year,weekstart.month,weekstart.day))
    mins = td.days*1440 + td.seconds//60
    return mins
def time_histogram(request):
    form = TimePersonForm(request.GET)
    if not form.is_valid():
        pass
    else:
        q = form.cleaned_data['q']
        use_regex = form.cleaned_data.get('regex', False)
        if use_regex:
            regex_pattern = re.compile(q, re.I)
        matches = get_time_slots(**form.cleaned_data)

        H = cava.util.Histogram()
        for slot in matches:
            intervals = cava.util.parseslot(slot.shift(), slot.name)
            for name, start, end in intervals:
                if not (   (not use_regex and q.lower() in name.lower())
                        or (    use_regex and regex_pattern.search(name) )):
                    continue
                start_mins = _time_since_weekstart(start)
                end_mins   = _time_since_weekstart(end)
                #if start_mins == 970 or end_mins == 970:
                #    print start_mins, end_mins
                if end_mins > start_mins:
                    H.add(start_mins, end_mins)
                else:
                    H.add(start_mins, 10080)
                    H.add(0, end_mins)
        plot_rows = [ (0, 0) ]
        rows = [ ]
        for time, count in H.rows():
            plot_rows.append((time/1440., plot_rows[-1][1]))
            rows.append(dict(count=count,
                             time=time,
                             day=time//1440,
                             hour=time%1440 // 60,
                             minute=time%60,
                             ))
            plot_rows.append((time/1440., count))

        img_path = request.get_full_path()+'&img=1'
        #print 'w'
        #for row in rows:
        #    pass
        #print 'x'
        #for t, c in plot_rows:
        #    if .5 < t < .8:
        #        print t, c
        #print 'y'
        #for t, c in H.rows():
        #    if 800 < t < 1200:
        #        print t, c

        if 'img' in request.REQUEST:
            import tempfile
            tmpdir = tempfile.mkdtemp()
            os.environ['MPLCONFIGDIR'] = tmpdir
            from matplotlib.backends.backend_agg import Figure, FigureCanvasAgg
            f = Figure()
            c = FigureCanvasAgg(f)
            ax  = f.add_subplot(111)
            ax.set_xlabel("Days (0=Monday, 1=Tuesday, etc)")
            ax.set_ylabel("Number of times on call")
            for dayx, day in zip((.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5),
                              "MTWTFSS"):
                ax.text(x=dayx, y=.5, s=day)
            ts, cs = zip(*plot_rows)
            ax.plot(ts, cs)
            ax.set_xlim(0, 7)
            for i in range(1, 7):
                ax.axvline(x=i, color='gray', linestyle='--')
            import cStringIO
            p = cStringIO.StringIO()
            c.print_figure(p, bbox_inches='tight')
            import shutil
            shutil.rmtree(tmpdir)
            response = HttpResponse(p.getvalue(), mimetype="image/png")
            return response

    template = django.template.loader.get_template("cava/time_histogram.html")
    body = template.render(RequestContext(request, locals()))
    return HttpResponse(body)
