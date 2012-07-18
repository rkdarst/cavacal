# Richard Darst, February 2011

import datetime

import cal.views as views
from django.core.urlresolvers import reverse

calendar_views = (views.month, views.month_edit)

import cava.util
from cava import bquotes
import cavapeople.views
import cal.models as models

def makeQueryStr(queries):
    if not queries: return ''
    return '?' + '&'.join(queries)

class NavBarMiddleware(object):
    def process_view(self, request, view, args, kwargs):
        request.month_bar = self.month_bar(request, view, kwargs)
        request.rank_bar  = self.rank_bar(request, view, kwargs, extra_links=0)
        request.edit_bar  = self.edit_bar(request, view, kwargs)
        if request.user.has_perm('cal.can_edit_calendar') \
           or view == views.month_edit:
            request.edit_bar_if_permission = request.edit_bar+'<br>'
        request.bquote = bquotes.get()


        request.sitebox = \
        ""\
        ""

        if "openiduser" in request.user.username:
            request.usermessage = '<b><a href="%s"><font color="red">Change your username!</font></a></b>'%reverse(cavapeople.views.change_username)

        request.pageheader = (''
#            '<center><font color="red"><b>'
#        'This is an unofficial calendar. '
#        'Data and changes here are not official but should be accurate.  '
#        'Send suggestions or '
#        'bugs/complaints to darst. '
#        'You can highlight your name in the schedule '
#        '<a href="%(highlight)s">here</a>. '
#        '<a href="%(about)s">About this calendar</a>.</b></font>'
#        '</center>'%dict(about=reverse('cal-about'),
#                         highlight=reverse(views.highlight))
            )

        motds = models.get_current_motds()
        if motds:
            request.motd = "; ".join(motds)


    def month_bar(self, request, view, kwargs):
        """Bar to change among different months

        Accessible from request.month_bar."""
        year = month = None
        date = datetime.date.today().replace(day=1)
        if kwargs.get('month', None) is not None:
            month = int(kwargs['month'])
            date  = date.replace(month=month)
        if kwargs.get('year', None) is not None:
            year = int(kwargs['year'])
            date = date.replace(year=year)
        bar = [ ]

        #
        if view not in calendar_views:
            view = views.month

        queries = [ ]
        for name in ('rank_id', ):
            if name in request.REQUEST:
                queries.append('%s=%s'%(name, request.REQUEST[name]))
        query_string = makeQueryStr(queries)

        for i in range(-3, 4):
            newdate = cava.util.increment_month(date, i)
            url = reverse(view, kwargs={'year':newdate.year, 'month':'%02d'%newdate.month})+query_string
            if newdate.year==year and newdate.month==month:
                text = '<font size="200%%">%s</font>'%(newdate.strftime('%B %Y'),)
                if view not in (views.month, views.month_edit):
                    text = '<a href="%s">%s</a>'%(url, text)
            else:
                text = '<a href="%s">%s</a>'%(url, newdate.strftime('%b'))
            bar.append(text)

        bar = ' - '.join(bar)
        return bar

    def rank_bar(self, request, view, kwargs, to_view=views.month,
                 extra_links=True):
        """Bar to change among different ranks

        Accessible from request.rank_bar."""
        bar = [ ]

        year = month = None
        date = datetime.date.today().replace(day=1)
        if kwargs.get('month', None) is not None:
            month = int(kwargs['month'])
            date  = date.replace(month=month)
        if kwargs.get('year', None) is not None:
            year = int(kwargs['year'])
            date = date.replace(year=year)

        queries = [ ]
        for name in ('start', 'end'):
            if name in request.REQUEST:
                queries.append('%s=%s'%(name, request.REQUEST[name]))

        if 'rank_id' in request.REQUEST:
            current_rank = int(request.REQUEST['rank_id'])
        elif to_view == views.month or to_view == views.month_edit:
            current_rank = -1
        else:
            current_rank = None

        if kwargs.get('month', None) is None:
            url = reverse('cal-month-future')
        else:
            url = reverse(to_view, kwargs={'year':date.year,
                                           'month':'%02d'%date.month})


        if current_rank == -1 and view == to_view:
            bar.append('<b>All ranks</b>')
        else:
            _url = url + makeQueryStr(queries)
            bar.append('<a href="%s">All ranks</a>'%(_url))

        for rank in views.ranks:
            _url = url + makeQueryStr(queries)
            if current_rank == rank.rank_id and view==to_view:
                bar.append('<b>%s</b>'%rank.rank)
            else:
                _url = url + makeQueryStr(queries+["rank_id=%d"%rank.rank_id])
                bar.append('<a href="%s">%s</a>'%(_url, rank.rank))

        if extra_links:
            search_link = reverse(views.search)
            bar.append('<font size=1><a href="%s">Search</a></font>'%
                                                                   search_link)
            log_link = reverse(views.log)
            bar.append('<font size=1><a href="%s">Log</a></font>'%log_link)

            export_link = reverse('cal.export.ical')
            bar.append('<font size=1><a href="%s">Export</a></font>'%export_link)

            highlight_link = reverse(views.highlight)
            bar.append('<font size=1><a href="%s">Highlight</a></font>'%highlight_link)
            about_link = reverse('cal-about')
            bar.append('<font size=1><a href="%s">About</a></font>'%about_link)

        bar = ' - '.join(bar)
        return bar


    def edit_bar(self, request, view, kwargs):
        #bar = [ ]
        bar = self.rank_bar(request, view, kwargs, to_view=views.month_edit,
                            extra_links=False)
        bar = '<b>Mass edit:</b> '+bar
        return bar
