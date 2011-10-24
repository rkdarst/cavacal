# Richard  Darst, October 2010

import datetime
import email
import email.mime
import email.mime.text
import re
import textwrap

EPOCH = datetime.date(1970,1,1)
RANKS = ('cc', 'driver', 'attendant', 'probie')
rank_d = {'cc':1, 'driver':2, 'attendant':3, 'probie':4}

class Shift(object):
    def __init__(self, shift_id=None, date=None, time=None):
        # Specifying the date and time:
        if (date is not None)and(time is not None):
            if isinstance(date, tuple):  # convert tuple to date object
                date = datetime.date(*date)
            time = time.lower()
            if time.lower() not in ('am', 'pm'):
                raise Exception('Time must be "am" or "pm".')
            shift_id = (date-EPOCH).days * 2
            if time == 'pm':
                shift_id += 1
            self.shift_id = shift_id
        # Specifying the integer shift id
        elif shift_id is not None and isinstance(shift_id, int):
            self.shift_id = shift_id
        else:
            raise Exception("Either year&month&day&time or shift must be specified.")
    def __int__(self):
        return self.shift_id
    def __hash__(self):
        return hash((self.__class__, self.shift_id))
    def __eq__(self, other):
        return self.shift_id == other.shift_id
    def __repr__(self):
        return "<Shift((%s), %s)>"%(self.date.strftime("%Y, %m, %d"), self.time)
    @property
    def previous(self):
        """The previous shift"""
        return Shift(shift_id=int(self)-1)
    @property
    def next(self):
        """The next shift"""
        return Shift(shift_id=int(self)+1)
    @property
    def date(self):
        day  = self.shift_id // 2
        date = EPOCH + datetime.timedelta(days=day)
        return date
    @property
    def time(self):
        time = self.shift_id % 2
        if time == 0: return 'am'
        if time == 1: return 'pm'

    def text(self):
        """Human readable text for shift"""
        return self.date.strftime("%b %d (%a) %%s")%self.time
    def exacttime(self):
        """Return exactly when this shift begins."""
        date = self.date
        time = datetime.datetime(date.year, date.month, date.day)

        AMstart        = {'hour': 8, 'minute':30}
        AMstartweekend = {'hour':10, 'minute':00}
        PMstart        = {'hour':20, 'minute':30}
        if datetime.date(2011,5,22) < date < datetime.date(2011,8,29):
            AMstart = {'hour': 7, 'minute': 00}
            PMstart = {'hour':19, 'minute': 00}

        if self.time == 'am':
            if date.weekday() in (5,6):
                return time.replace(**AMstartweekend)
            else:
                return time.replace(**AMstart)
        else:
            return time.replace(**PMstart)
    start = exacttime
    def end(self):
        """Return the time this shift ends (start of next shift)"""
        return self.next.exacttime()
    def timeuntil(self):
        return self.exacttime() - datetime.datetime.now()
    def is_weekend(self):
        """True if this shift is considered a weekend shift."""
        weekday = self.date.weekday()
        if weekday in (3,4) and self.time == 'pm':
            return True
        if weekday in (5,6):
            return True
        return False

def get_current_shift(now=None):
    if now is None:
        now = datetime.datetime.now()
    shift = Shift(date=now.date(), time="am")
    while True:
        if shift.exacttime() > now:
            shift = shift.previous
        elif shift.next.exacttime() <= now:
            shift = shift.next
        else:
            break
    return shift

#def break_shift(shift, name):
#    """Break up a shift into its component parts.
#    """
#    components = [ ]
#    m = re.match('\(.*\)', name)
#    if m:
#        components.append[m.group()]
#        name = name[:m.start()] + name[m.end():]

class Member(object):
    def __init__(self, name, email, regex):
        self.name = name
        self.email = email
        self.regex = re.compile(regex, re.I)
    def match(self, shift):
        if self.regex.search(shift):
            return True
        return False

members = [
    Member('Richard Darst', 'rkd2107@columbia.edu', 'richard|darst'),
    Member('Alexander Harstrick', 'rkd+ah@zgib.net', 'harstrick'),
    Member('Keva Garg', 'rkd+kg@zgib.net', 'keva|garg'),
    Member('Fernando Rios', 'rkd+fr@zgib.net', 'fernando|rios'),
    Member('Laura Trujillo', 'let2109@columbia.edu', 'laura'),
    Member('Sara Schilling', 'shs2136@columbia.edu', 'schilling'),
    ]

def findSlotMembers(slot):
    """Return a list of member objects for each member assigned to a shift
    """
    slotMembers = [ ]
    for member in members:
        if member.match(slot):
            slotMembers.append(member)
    return slotMembers


class Schedule(object):
    _dates = {
        # 29806 = Shift(2010,10,21, 'am')
        29806: {'cc':'harstrick','driver':'','attendant':'','probie':'darst'},
        29807: {'cc':'','driver':'','attendant':'','probie':'hannah'},
        None: {'cc':'','driver':'','attendant':'','probie':''},
        }
    def __init__(self, members):
        self.members = members
    def __getitem__(self, key):
        if key in self._dates:
            return self._dates[key]
        return {'cc':'','driver':'','attendant':'','probie':''}

    def findSlotMembers(self, slot):
        """Return a list of member objects for each member assigned to a shift
        """
        slotMembers = [ ]
        for member in members:
            if member.match(slot):
                slotMembers.append(member)
        return slotMembers

    def emailDate(self, shift_id):
        shiftMembers = self[shift_id]
        emails =  [ ]
        for rank in RANKS:
            slotMembers = self.findSlotMembers(shiftMembers[rank])
            for member in slotMembers:
                emails.append(self.reminderEmail(
                    member=member,
                    shift_id=shift_id,
                    slotRank=rank))
        return emails

    def reminderEmail(self, member, shift_id, slotRank):

        shift = Shift(shift_id=shift_id)
        shiftMembers = self[shift_id]
        shiftMembersBefore = self[shift_id-1]
        shiftMembersAfter  = self[shift_id+1]
    
        # Oct 21 PM (Wed)
        time = shift.time
        datestr = shift.date.strftime('%b %d %%s (%a)')%time
        
        body = textwrap.dedent("""\
        You have a %(slotRank)s shift on %(date)s.
    
        Your crew:
          CC:        %(cc)s
          Driver:    %(driver)s
          Attendant: %(attendant)s
          Probie:    %(probie)s
    
        Before you:
          Before: %(before)s
    
        After you:
          After: %(after)s
    
        LINK_HERE
        (%(shift_id)s)
        """)%{'date': datestr,
             'slotRank': slotRank,
              'cc':        shiftMembers['cc'],
              'driver':    shiftMembers['driver'],
              'attendant': shiftMembers['attendant'],
              'probie':    shiftMembers['probie'],
              'before': shiftMembersBefore[slotRank],
              'after':  shiftMembersAfter[slotRank],
              'shift_id':shift_id
              }
        msg = email.mime.text.MIMEText(body)
        msg["To"] = '%s <%s>'%(member.name, member.email)
        msg["From"] = 'CU-EMS Reminder <rkd@zgib.net>'
        msg["Subject"] = '%s shift, %s'%(slotRank, datestr)
        return msg

def increment_month(date, increment=1):
    """Intelligently increment the month
    """
    year, month = date.year, date.month
    month -= 1  # months index at 1, module indexes at 0
    yearincrement, month = divmod(month+increment, 12)
    year += yearincrement
    month += 1
    return datetime.date(year, month, 1)


bracket_re = re.compile(r'\[[^]]*\]')
paren_re   = re.compile(r'\([^)]*\)')
split_re   = re.compile(r'/+')
time_re    = re.compile(r'(\d{1,2}):?(\d{2})$')
def _maketime(string):
    m = time_re.match(string)
    if not m:
        return None
    return datetime.time(int(m.group(1)), int(m.group(2)))
def _getsecs(t):
    return t.hours*3600 + t.minutes*60 + t.seconds + t.microseconds/1e6
def _getrealtime(start, t):
    """Convert a shift and a time into the actual time it represents."""
    newt = start.replace(hours=t.hours,
                         minutes=t.minutes,
                         seconds=t.seconds)
    dt = abs(_getsecs(shift.start().time()) - getsecs(t))
    if dt > 12*3600:
        # We need to wrap around
        if start.hour < 12:
            # Morning time, wrap around to previous night
            newt -= datetime.timedelta(days=1)
        else:
            pass
def parseslot(shift, slot):
    slot = slot.strip()
    slot = bracket_re.sub('', slot)
    slot = paren_re.sub('', slot)
    parts = split_re.split(slot)

    curtime = None
    name = None

    for part in parts:
        t = matchtime(part)
        if t is not None:
            # Handle a time
            pass
        # Handle a name
        pass



#def parseShift(text, xm='am'):
#    text = re.sub('\([^)]*\)', '', text)
#    print re.split('[^a-z0-9:-]*', text, re.I)
#    print text

if __name__ == "__main__":
    #parseShift("richard//2000//laura(sarah)")
    print int(Shift(2010,10,21, 'am'))

    cava = Schedule(members=members)

    msgs = cava.emailDate(29806)
    for msg in msgs:
        print msg
    #from fitz import interactnow
