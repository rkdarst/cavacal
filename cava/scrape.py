# Richard Darst, January 2011

import hashlib
import httplib
import datetime
import cPickle as pickle
import re
import textwrap
import urllib

from django.core.mail import mail_admins
import mechanize

import util

pageRE = re.compile(r"""<td[^>]*><div.class='daynum'>([0-9]+)</div><br>\s*
AM:\s*(.*?)\s*<br>\s*
PM:\s*(.*?)\s*
</td>""",
               re.VERBOSE )

def iterCalendarPage(page):
    for day, AM, PM in pageRE.findall(page):
        yield int(day), AM.strip(), PM.strip()
def getUrl(host, URL, params={}):
    """Make a raw HTTP request without redirection

    if params is given, this will be a POST request.
    """
    phpsessid = hashlib.md5(datetime.date.today().strftime(
                                            '%Y-%m-%d-knto6NTkro')).hexdigest()
    headers = {"Cookie":"PHPSESSID=%s"%phpsessid,
               "User-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; "
                             "rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
               }
    if params:
        params = urllib.urlencode(params)
        headers["Content-type"] = "application/x-www-form-urlencoded"
        method = "POST"
    else:
        method = "GET"
    # Create a phpsessid based on the hash of today.
    conn = httplib.HTTPConnection(host)
    conn.request(method, URL, params, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return data, response

class Scraper(object):
    def __init__(self, username=None, password=None):
        if username:
            self.br = mechanize.Browser()
            self.br.open("http://www.cuems.org/members.php")

            self.br.select_form(nr=0)
            self.br["username"] = username
            self.br["password"] = password
            r = self.br.submit()
        else:
            self.br = None

        self.schedule = Schedule()
        self._been_scraped = set()
    def __getitem__(self, key):
        shift, rank = key
        date = shift.date
        if (date.year, date.month) not in self._been_scraped:
            self.load(date.year, date.month)
            self._been_scraped |= set(((date.year, date.month), ))
        return self.schedule[key]
    def load(self, year, month):
        loadFromWeb(self.schedule, self, year=year, month=month)

    def getmonth(self, year, month, rank_id):
        url = 'http://www.cuems.org/cal/index.php?date=%(year)04d-%(month)02d&rank=%(rank_id)d'%{'month':month, 'year':year, 'rank_id':rank_id}
        #print "getting:", year, month, rank_id
        if self.br:
            r = self.br.open(url)
            data = r.read()
        else:
            data, response = \
                  getUrl("www.cuems.org", url.split("www.cuems.org")[1])
            for weekday in ("Sunday", "Monday", "Tuesday", "Wednesday",
                            "Thursday", "Friday", "Saturday"):
                if weekday not in data:
                    raise Exception("Invalid data in calendar page.")
        for day, AM, PM in iterCalendarPage(data):
            yield day, 'am', AM
            yield day, 'pm', PM


class Schedule(object):
    """Dummy schedule to set and store items.
    """
    def __init__(self):
        self._data = { }
    def __setitem__(self, key, value):
        self._data[key] = value
    def __getitem__(self, key):
        return self._data[key]

    def printall(self):
        keys = self._data.keys()
        keys.sort(key=lambda x: (x[0].shift_id,x[1]))
        #keys = set((y, m, d, h) for y,m,d,h,r in keys)
        #keys = list(keys)
        #keys.sort()
        for key in keys:
            print key[0], key[1], self[key]


def loadFromWeb(schedule, scraper, year=None, month=None):
    if year is None:
        year = datetime.date.today().year
    if month is None:
        month = datetime.date.today().month
    elif isinstance(month, str):
        monthDelta = int(month)
        month = datetime.date.today().month
        month -= 1
        month += monthDelta
        yearDelta, month = divmod(month, 12)
        year += yearDelta
        month += 1
    # blah
    for rank_id in (1, 2, 3, 4):
        for day, time, shift in scraper.getmonth(year, month, rank_id):
            schedule[util.Shift(date=(year,month,day),time=time),rank_id]=shift

class Schedule2(object):
    """Dummy schedule to set and store items.

    Uses the more efficient sync-gateway.
    """
    def __init__(self,
                 first_date=datetime.datetime(2011,9,1),
                 last_date=None):
        self.first_date = first_date
        self.last_date  = last_date
        self._data = { }
        for shift, rank_id, name in \
                          loadFromWeb2(first_date=first_date,
                                       last_date=last_date):
            self._data[shift, rank_id] = name

    def __setitem__(self, key, value):
        self._data[key] = value
    def __getitem__(self, key):
        """
        KeyError - not set on the upstream calendar.
        ValueError - domain error: trying to get a slot which wasn't
                     included in scraping.
        """
        shift, rank_id = key
        if shift.date < self.first_date:
            raise ValueError("Date is too early")
        if self.last_date is not None and shift.date > self.last_date:
            raise ValueError("Date is too late")
        return self._data[key] # KeyError if not here.

    def printall(self):
        keys = self._data.keys()
        keys.sort(key=lambda x: (x[0].shift_id,x[1]))
        #keys = set((y, m, d, h) for y,m,d,h,r in keys)
        #keys = list(keys)
        #keys.sort()
        for key in keys:
            print key[0], key[1], self[key]


def loadFromWeb2(first_date=datetime.datetime(2011,9,1), last_date=None):
    """This loads from the web using my sync gateway (more efficient, faster)
    """
    first_date = first_date.strftime('%Y-%m-%d')

    url = 'http://www.cuems.org/cal/raw.py?first_date=%s'%first_date
    if last_date:
        last_date  = last_date.strftime('%Y-%m-%d')
        url += '&last_date='+last_date

    import urllib
    for line in urllib.urlopen(url):
        if line.startswith('#'):
            continue
        d, xm, rank_id, name = line.split('\t')
        name = name.strip()
        yield util.Shift(date=datetime.datetime.strptime(d, '%Y-%m-%d').date(),
                         time=xm), int(rank_id), name

def pushchange(date, time, rank, name):
    # http://www.cuems.org/cal/index.php?edit=1:2011-09-02:PM
    params = {'schedinfo[date]':date.strftime('%Y-%m-%d'),
              'schedinfo[shift]':time.upper(),
              'schedinfo[rank]':int(rank),
              'schedinfo[name]':name.strip()}
    data, response = getUrl("www.cuems.org", "/cal/", params=params)


    # Do testing to establish that we successfully pushed the data.
    #data = response.read()
    push_successful = True
    for weekday in ("Sunday", "Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday", "Saturday"):
        if weekday not in data:
            push_successful = False
    if not push_successful:
        status = response.status
        reason = response.reason
        mail_admins(
            subject="Push failed, %s %s"%(status, reason),
            message=textwrap.dedent("""\
                date: %(date)s
                time: %(time)s
                rank: %(rank)s
                new-name: %(name)s
                response.status: %(status)s
                response.reason: %(reason)s

                %(data)s
                """%locals()),
            )
    return response


if __name__ == "__main__":
    #data = open("cavacal-2011-01.html").read()
    #print r.findall(data)

    query = 0
    filename = 'scrapedcal.pickle'
    if query:
        #scr = Scraper(*open("/home/richard/.private/cavapwd").read().split())
        scr = Scraper()
        sch = Schedule()
        loadFromWeb(sch, scr)
        #loadFromWeb(sch, scr, month="+1")
        #loadFromWeb(sch, scr, month="+2")
        pickle.dump(sch, open(filename, 'w'))
    else:
        sch = pickle.load(open(filename))
    sch.printall()
    
    #from fitz import interactnow
