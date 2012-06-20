# Richard  Darst, October 2010

import datetime
import email
import email.mime
import email.mime.text
import math
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
        #if datetime.date(2011,5,22) < date < datetime.date(2011,8,29):
        #    AMstart = {'hour': 7, 'minute': 00}
        #    PMstart = {'hour':19, 'minute': 00}
        # Handle the summer shift changes:
        if not 5 <= date.month <= 8:
            # Not summer time, do nothing in this if branch.
            pass
        elif date.year >= 2012 \
             and not (    ( date.month==5 and date.day<23 )
                       or ( date.month==8 and date.day>25 ) ):
                 AMstart = {'hour': 7, 'minute': 00}
                 PMstart = {'hour':19, 'minute': 00}
        elif date.year == 2011 \
              and datetime.date(2011,5,22) < date < datetime.date(2011,8,29):
            AMstart = {'hour': 7, 'minute': 00}
            PMstart = {'hour':19, 'minute': 00}

        # Weekend AM start times.
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
        if weekday == 5:
            return True
        if weekday == 6 and self.time == 'am':
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
def _matchtime(string):
    m = time_re.match(string)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2))
    if hour >= 24:
        hour -= 24
    time = datetime.time(hour, minute)
    return time
def _getsecs(t):
    return t.hour*3600 + t.minute*60 + t.second + t.microsecond/1e6
def _getrealtime(start, t, backwards=False):
    """Convert a datetime and a time into the actual time it represents."""
    #newt = start.replace(hours=t.hours,
    #                     minutes=t.minutes,
    #                     seconds=t.seconds)
    dt = _getsecs(t) - _getsecs(start)
    dt1 = dt
    if backwards:
        dt = dt - ((dt+43200) // (86400)) * (86400)
    else:
        dt = dt - ((dt+0) // (86400)) * (86400)
    dt2 = dt
    dt = datetime.timedelta(seconds=dt)
    return start + dt
def parseslot(shift, slotcontents):
    slot = slotcontents.strip()
    slot = bracket_re.sub('', slot)
    slot = paren_re.sub('', slot)
    parts = split_re.split(slot)

    curtime = shift.start()
    name = ''
    shift_people = [ ] # List of lists [name, start, end]
    last_part=None

    for i, part in enumerate(parts):
        if not part.strip():
            continue
        t = _matchtime(part)
        if t is not None:
            # Handle a time
            curtime = _getrealtime(curtime, t,
                            backwards=True if len(shift_people)==0 else False)
            #if len(shift_people) > 0:
            #    shift_people[-1][2] = curtime
            for row in shift_people:
                if row[2] == None:
                    row[2] = curtime
            last_part = "time"
        else:
            # Handle a name
            name = part.strip()
            shift_people.append([name, curtime, None])
            last_part = "name"
    if last_part == "time":
        shift_people[-1][2] = curtime
        for row in shift_people:
            if row[2] == None:
                row[2] = curtime
    elif last_part == "name":
        #shift_people[-1][2] = shift.end()
        for row in shift_people:
            if row[2] == None:
                row[2] = shift.end()

    return shift_people

def makediff(s1, s2):
    """Diff two shifts, returning new two-string diff."""
    import difflib
    differ = difflib.SequenceMatcher()
    differ.set_seqs(s1, s2)
    #debug = False
    #if s2 == "Allie//1200/Ruth//1700/Harstrick":
    #    debug = True
    #for op, i1, i2, j1, j2 in reversed(differ.get_opcodes()):
    #if debug: print "start"
    s1new = [ ]
    s2new = [ ]
    previousOp = None
    for op, i1, i2, j1, j2 in differ.get_opcodes():
        #if debug: print "top"
        #if debug: print op, i1, i2, j1, j2, '->'
        #if debug: print s1, s2
        if op == 'equal':
            if i2-i1 < 4 and len(s1new) > 1 and previousOp == "replace":
                s1new[-2] += s1[i1:i2]
                s2new[-2] += s2[j1:j2]
            else:
                s1new.append(s1[i1:i2])
                s2new.append(s2[j1:j2])
        elif op == 'insert':
            s2new.extend(('<b>', s2[j1:j2], '</b>'))
        elif op == "delete":
            s1new.extend(('<strike>', s1[i1:i2], '</strike>'))
        elif op == 'replace':
            s1new.extend(('<strike>', s1[i1:i2], '</strike>'))
            s2new.extend(('<b>', s2[j1:j2], '</b>'))
        previousOp = op
        #if debug: print s1, s2
        #if debug: print "bottom"
    #if debug: print "done"
    return ''.join(s1new), ''.join(s2new)


class Histogram(object):
    def __init__(self):
        self.times = [ ]
        self.counts = [ ]
    def _insert_index(self, index, time):
        self.times.insert(index, time)
        if index == 0:
            value = 0
        else:
            value = self.counts[index-1]
        self.counts.insert(index, value)
    def _find_time_index(self, time):
        """Find time index, add it if needed, return index"""
        try:
            index = self.times.index(time)
        except ValueError:
            index = 0
            while True:
                if index >= len(self.times):
                    self._insert_index(len(self.times), time)
                    break
                if self.times[index] > time:
                    self._insert_index(index, time)
                    break
                index += 1
        return index
    def add(self, start, end, value=1):
        """Add value between start and end."""
        index_start = self._find_time_index(start)
        index_end = self._find_time_index(end)
        for i in range(index_start, index_end):
            self.counts[i] += value
    def rows(self):
        """Return [(t0, c0), (t1, c1), ...]"""
        return zip(self.times, self.counts)

def _test_histogram():
    H = Histogram()
    H.add(0, 5)
    print H.rows()
    H.add(3, 10)
    H.add(1, 5)
    H.add(2, 5)
    print H.rows()

#def parseShift(text, xm='am'):
#    text = re.sub('\([^)]*\)', '', text)
#    print re.split('[^a-z0-9:-]*', text, re.I)
#    print text

if __name__ == "__main__":
    #parseShift("richard//2000//laura(sarah)")
    #print int(Shift(2010,10,21, 'am'))

    #cava = Schedule(members=members)

    #msgs = cava.emailDate(29806)
    #for msg in msgs:
    #    print msg
    #from fitz import interactnow

    _test_histogram()
