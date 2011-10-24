from django.db import models
from django.db.models import Q, Max
from django.contrib.auth.models import User, AnonymousUser
# Create your models here.

import datetime
import os
import sys
import thread

import cava.util
import cava.scrape

class Permissions(models.Model):
    """This is a placeholder class to have permissions on"""
    class Meta:
        permissions = (
            ('can_view_calendar', 'Can view the calendar'),
            ('can_edit_calendar', 'Can edit the calendar'),
            )


class Rank(models.Model):
    def __unicode__(self):
        return self.rank
    rank_id = models.IntegerField(primary_key=True)
    rank = models.CharField(max_length=32, unique=True)

class Slot(models.Model):
    def __unicode__(self):
        return ",".join((str(self.shift_id), self.rank.rank, self.name))
#    shift_rank_id = models.IntegerField(primary_key=True)
    shift_id = models.IntegerField()
    rank     = models.ForeignKey(Rank)
    name     = models.CharField(max_length=256)
    changed_by = None
    def __init__(self, *args, **kwargs):
        # Save original contents (for transaction log)
        super(Slot, self).__init__(*args, **kwargs)
        self._original_name = self.name

    def save(self, *args, **kwargs):
        # Save transaction log
        super(Slot, self).save(*args, **kwargs)
        # Don't save if changed_by is false
        if self.changed_by == False:
            return
        log= LogSlot(shift_id=self.shift_id,
                rank=self.rank,
                name_old=self._original_name,
                name_new=self.name)
        if isinstance(self.changed_by, AnonymousUser):
            log.changer = None
        elif isinstance(self.changed_by, str):
            log.changer_username = self.changed_by
        else:
            log.changer = self.changed_by # defaults to None
        log.save()
    def shift(self):
        return cava.util.Shift(shift_id=self.shift_id)

class LogEmail(models.Model):
    ctime    = models.DateTimeField(auto_now_add=True)
    version  = models.IntegerField()
    shift_id = models.IntegerField()
    rank     = models.ForeignKey(Rank)
    sent_to  = models.CharField(max_length=256,null=True)
    hash     = models.IntegerField(null=True)
    text     = models.CharField(max_length=256,null=True)


class LogSlot(models.Model):
    shift_id = models.IntegerField()
    rank     = models.ForeignKey(Rank)
    name_old = models.CharField(max_length=256, null=True)
    name_new = models.CharField(max_length=256)
    mtime    = models.DateTimeField(auto_now_add=True)
    changer  = models.ForeignKey(User, null=True)
    changer_username  = models.CharField(max_length=32, null=True)
    def shift(self):
        return cava.util.Shift(shift_id=self.shift_id)
    def prettymtime(self):
        return self.mtime.strftime('%b %d, %H:%M')
    def name_old_if_different(self):
        if self.name_old == self.name_new:
            return "-"
        else:
            return self.name_old
    def prettychanger(self):
        if self.changer:
            return self.changer.username
        elif self.changer_username:
            return self.changer_username
        else:
            return ''


class Schedule(object):
    def __init__(self, cache=None):
        if cache:
            self.cache = { }
            low, high = cache
            slots = Slot.objects.filter(shift_id__gte=low,
                                       shift_id__lte=high)
            for slot in slots:
                self.cache[slot.shift_id, slot.rank_id] = slot
        else:
            self.cache = None
    def __getitem__(self, key):
        shift, rank = key
        shift_id = int(shift)
        if self.cache and (shift_id, rank.rank_id) in self.cache:
            return self.cache[shift_id, rank.rank_id].name

        slot = Slot.objects.filter(shift_id=shift_id, rank=rank)
        if len(slot) == 0:  return ''
        else:               return slot[0].name

    def __setitem__(self, key, value, user=None, push=True):
        shift, rank = key
        shift_id = int(shift)
        if isinstance(rank, int):
            rank = Rank.objects.filter(rank_id=rank)[0]

        try:
            slot = Slot.objects.get(shift_id=int(shift), rank=rank)
            if slot.name == value:
                return
            slot.name = value
        except Slot.DoesNotExist:
            if not value:
                return
            slot = Slot(shift_id=shift_id, rank=rank, name=value)

        if user:
            slot.changed_by = user
        elif hasattr(self, "user"):
            slot.changed_by = self.user
        #slot.changed_by = False  # This prevents logging
        slot.save()

        # Push to upstream  - we have already returned above if there
        # is no change.
        shift = cava.util.Shift(shift_id)
        kwargs = {'date':shift.date,
                'time':shift.time,
                'rank':rank.rank_id,
                'name':value}

        #push = False  # This prevents pushing changes upstream
        if push:
            cava.scrape.pushchange(shift.date, shift.time, rank.rank_id,value)
            # CGI running does not take nicely to threading.
            #thread.start_new_thread(cava.scrape.pushchange, (shift.date,
            #shift.time, rank.rank_id, value))
            # Django does *not* like being forked.  Figure out why.  I think it
            # has to do with trapping SystemExit and not letting it
            #if os.fork() == 0:
            #    sys.stdout = sys.stderr = open('/srv/cava/push.log', 'a')
            #    cava.scrape.pushchange(shift.date, shift.time,
            #                           rank.rank_id,value)
            #    os._exit()

    setslot = __setitem__
    def has_key(self, key):
        shift, rank = key
        shift_id = int(shift)

        slots = Slot.objects.filter(shift_id=shift_id, rank=rank)
        return len(slots)



class Motd(models.Model):
    # field "id" for primary key.
    message  = models.CharField(max_length=1024, null=True, blank=True)
    start    = models.DateTimeField(null=True, blank=True,
                           verbose_name="first date to show this message"
                                    " (YYYY-MM-DD [HH:MM])")
    end      = models.DateTimeField(
                           verbose_name="last date to show this message")
    type     = models.IntegerField(default=1,
                                   choices=((1, "All pages"),
                                            ))
    enabled  = models.BooleanField(default=1)
    @property
    def visible(self):
        now = datetime.datetime.now()
        if (self.message
            and (not self.start or self.start <= now)
            and (not self.end   or self.end >= now)
            and self.enabled):
            return True
        return False

def get_current_motds():
    now = datetime.datetime.now()
    motds = Motd.objects.filter(Q(start__isnull=True) | Q(start__lte=now),
                                Q(end__isnull=True)   | Q(end__gte=now),
                                Q(message__isnull=False),
                                enabled=True).order_by('-id')
    if motds.count() == 0:
        return None
    return [ m.message for m in motds if m.visible ]

def last_modified():
    """Return datetime object of the last modification to calendar.

    Used in conditional view processing / time stamping
    """
    x = LogSlot.objects.all().aggregate(Max('mtime'))
    return x['mtime__max']

def slot_search(pattern, regex=False, **kwargs):
    if regex:
        matches = Slot.objects.filter(name__iregex=pattern, **kwargs)
    else:
        matches = Slot.objects.filter(name__icontains=pattern, **kwargs)
    return matches


