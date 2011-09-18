from django.core.management.base import BaseCommand, CommandError

import cPickle as pickle
import datetime
import optparse
import os
import sys

from cava.util import Shift, increment_month
import cava.scrape
import cal.models
import cal.views

class Command(BaseCommand):
    args = '[--fast]'
    help = "Scrape http://www.cuems.org/cal/ and store in our database"
    option_list = BaseCommand.option_list + (
        optparse.make_option('--fast',
                    action='store_true',
                    default=False,
                    help='Get only changes in the next few days.'),
        )

    def handle(self, *args, **kwargs):
        verbosity = int(kwargs['verbosity'])
        if verbosity >= 2:
            print kwargs
        
        #userpass = open("/home/richard/.private/cavapwd").read().split()
        scraper = cava.scrape.Scraper() #*userpass)
        
        zgibSch = cal.models.Schedule()
        zgibSch.user = "websync"
        #zgibSch.user = False  # makes it not log
        today = datetime.date.today()
        firstDate = today - datetime.timedelta(days=1)
        firstDate = firstDate.replace(day=1)

        
        # Get this month and next month
        firstShift = Shift(date=firstDate, time='am')
        lastShift=Shift(date=increment_month(today, increment=5),
                        time='am')
        if kwargs['fast']:
            if verbosity >= 2:
                print "--fast enabled"
            if (today + datetime.timedelta(days=2)).month == today.month:
                # If next month is more than two days away, then only
                # grab this month.
                lastShift=Shift(
                    date=increment_month(today,increment=1),
                    time='am')

        # All time
#        firstShift = Shift(date=(2006,1,1), time='am')

        if verbosity >= 2:
            print firstShift, lastShift
        numberChanged = 0
        shift = firstShift
        for i in range(5000):
            if verbosity >= 2:
                print shift
            for rank in cal.views.ranks:
                try:
                    slot = scraper[shift, rank.rank_id]
                except KeyError:
                    slot = ''
                # Do not re-save if it is already the same
                if slot == zgibSch[shift.shift_id, rank]:
                    continue
                if verbosity >= 1:
                    print "*", shift, rank, slot, "     (was: %s)"%\
                                                  zgibSch[shift.shift_id, rank]
                zgibSch[shift, rank] = slot
                numberChanged += 1
            shift = shift.next
            if shift.shift_id >= lastShift.shift_id:
                break

        if verbosity >= 1 and numberChanged > 0:
            print "total changed:", numberChanged
        sys.exit(0)
