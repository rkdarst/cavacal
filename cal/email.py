# Richard Darst, Feburary 2011

import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context
import django.template

from cava.util import Shift, members
from cal.models import Slot, Schedule, LogEmail


sendInterval = datetime.timedelta(hours=18)


class Email(object):
    def __init__(self, slot, member):
        self.slot = slot
        self.member = member

    def sent(self):
        log = LogEmail.objects.filter(shift_id=self.slot.shift_id,
                                      rank=self.slot.rank,
                                      sent_to=self.member.email)
        if len(log) > 0: return True
        return False
    def sent_exact(self):
        log = LogEmail.objects.filter(shift_id=self.slot.shift_id,
                                      rank=self.slot.rank,
                                      sent_to=self.member.email,
                                      text=self.slot.name)
        if len(log) > 0: return True
        return False
    def do_send(self):
        if self.slot.needssending and not self.sent_exact():
            return True
        return False


def email(request, send=False):
    """Main email handler.  Print a status on things."""
    REQUEST = request.REQUEST

    now = datetime.datetime.now()
    now_shift = Shift(date=now.date(), time='am')

    querySlots = Slot.objects.filter(shift_id__gte=int(now_shift))
    querySlots.order_by('shift_id', 'rank__rank_id')
    #slots = [ s for s in slots
    #          if s.shift().exacttime() > now-sendInterval ]

    slots = [ ]
    emails = [ ]
    for slot in querySlots:
        if slot.shift().exacttime() < now:
            continue
        if slot.shift().timeuntil() > datetime.timedelta(hours=24):
            continue
        slots.append(slot)
        for member in members:
            if member.match(slot.name):
                emails.append(Email(slot, member))
        #slot.interval = slot.shift().exacttime() - now
        # Is this proximate enough to send?
        #if slot.interval < sendInterval:
        #    slot.needssending = True
        #else:
        #    slot.needssending = False
        #members = slot.members = cava.findSlotMembers(slot.name)
        #
        #for member in members:
        #    emails.append(Email(slot=slot, member=member))
        #try: del member # remove loop variable for safety
        #except NameError: pass
    #try: del slot # remove loop variable for safety
    #except NameError: pass

    #calemail.marksent(slots[0])
    t = django.template.loader.get_template("email.html")
    body = t.render(Context(locals()))

    if send:
        to_send = [ ]
        for email in emails:
            # Make a list of what actually needs sending
            if not email.do_send():
                continue
            #objs = LogEmail.objects.filter(shift_id=email.slot.shift_id,
            #                               rank=email.slot.rank,
            #                               sent_to=email.member.email,
            #                               text=slot.name)
            to_send.append(email)
            
        # Send them
        for email in to_send:
            # make mails
            # send them
            pass
        # Log what we sent
        for email in to_send:
            # Log them all.
        
            LogEmail(version=1,
                     shift_id=email.slot.shift_id,
                     rank=email.slot.rank,
                     sent_to=email.member.email,
                     text=email.slot.name).save()
        
        return HttpResponseRedirect('/cal/email/')

    return HttpResponse(body)
