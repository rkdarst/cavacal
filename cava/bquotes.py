# Richard Darst, February 2011

import os
import random
import re


# strip <a> tags

cache_lines = [ ]

def load():
    if len(cache_lines) > 0:
        return cache_lines

    data =  open(os.path.join(os.path.dirname(__file__),'bquotes.txt')).read().split('\n')
    cache_lines.extend(data)
    return cache_lines
    
    

    data = open(os.path.join(os.path.dirname(__file__), 'bquotes.html')).read()
    data = re.sub(r'</?[a][^>]*>', '', data)
    data = re.sub(r'</?[bi]>', '', data)
    
    r = re.compile(r'<dd>([a-z]+): (.*?)</dd>', re.I)
    matches = r.findall(data)
    
    # List of all names
    names = set(group[0].lower() for group in matches)
    names -= set(('adam all amy andrew cassie demon doctor '\
                  'guardian jack judge psychiatrist soldier '\
                  'thomas vampire'.split()))
    names += set(('slayer buffybot'.split()))
    re_names = re.compile(r'\b'+('|'.join(names))+r'\b', re.I)

    for name, line in matches:
        if re_names.search(line): continue
        #print name, line
        cache_lines.append(line)
    return cache_lines
        
def get():
    return random.choice(load())

if __name__ == "__main__":
    for line in load():
        print line
