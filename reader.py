#!/usr/bin/env python3

import sqlite3
import sys
import os
import time
import random
import re
import urllib
import json
from pprint import pprint
import feedparser

os.chdir(os.path.dirname(os.path.abspath(__file__)))
db_name = 'rss.db'
debug = False
just_one = False
dry_run = False
days = None
url = None
grep = None
grepv = None
tagcontent = None
skipuntagged = False

def open_connection():
    return sqlite3.connect(db_name)
def close_connection(db):
    db.close()

def table_exists(db, table):
    c = db.cursor()
    query = c.execute('''SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?''', (table,))
    result = query.fetchone()
    if result[0] == 0:
        return False
    else:
        return True

def add_column(cursor, column):
    try:
        cursor.execute('''ALTER TABLE RSS ADD COLUMN ''' + column)
    except sqlite3.OperationalError:
        pass

def db_init():
    db = open_connection()
    try:
        c = db.cursor()
        if not table_exists(db, 'Stock'):
            c.execute('''CREATE TABLE IF NOT EXISTS RSS (guid text primary key)''')
        add_column(c, 'readdate datetime')
        add_column(c, 'tags text')
        add_column(c, 'ignored integer')
    except:
        print('failed to initialize database')
        raise
    db.commit()
    close_connection(db)


def is_read(db, guid):
    c = db.cursor()
    query = c.execute('''SELECT count(*) FROM RSS WHERE guid=?''', (guid,))
    result = query.fetchone()
    if result == None:
        return False
    if result[0] == 0:
        return False
    return True
    
def set_read(db, guid, tags):
    c = db.cursor()
    query = c.execute('''INSERT OR REPLACE INTO RSS(guid, readdate, tags) VALUES (?, datetime('now'), ?)''', (guid, json.dumps(tags)))
    db.commit()

def set_ignored(db, guid):
    c = db.cursor()
    query = c.execute('''INSERT OR REPLACE INTO RSS(guid, readdate, ignored) VALUES (?, datetime('now'), 1)''', (guid,))
    db.commit()

def get_value_from(entry, value, default):
    if isinstance(value, list):
        for attempt in value:
            if attempt in entry:
                return entry[attempt]
    elif isinstance(value, str):
        if value in entry:
            return entry[value]
    return default

# Process command line flags
for arg in sys.argv[1:]:
    if arg == '--debug':
        debug = True
    elif arg == '--1':
        just_one = True
    elif arg == '--dry-run':
        dry_run = True
    elif arg.startswith('--days='):
        try:
            days = int(arg[7:])
        except:
            print("Please use --days=<number>.")
            sys.exit(1)
    elif arg.startswith('--grep='):
        grep = arg[7:]
    elif arg.startswith('--grepv='):
        grepv = arg[8:]
    elif arg.startswith('--tag-content='):
        tagcontent = arg[14:]
    elif arg == '--skip-untagged':
        skipuntagged = True
    else:
        url = arg
if url == None:
    print('No URL specified, exiting.')
    sys.exit(1)

if skipuntagged and tagcontent is None:
    print('You must provide a regex with --tag-content to be able to skip untagged items.')
    sys.exit(1)

db_init()
db = open_connection()
d = feedparser.parse(url)

delay = False

for entry in d['entries']:
    if debug:
        pprint(entry)

    guid = get_value_from(entry, ['guid', 'id', 'link', 'title'], None)
    if guid is None:
        continue
    if is_read(db, guid):
        continue
    
    if days is not None:
        entry_time = time.mktime(entry['published_parsed'])
        now = time.time()
        if (now - entry_time) > days * 86400:
            continue
    if grep is not None:
        if re.search(grep, guid) is None:
            continue
    if grepv is not None:
        if re.search(grepv, guid) is not None:
            continue
    
    title = get_value_from(entry, 'title', '')
    published = '(' + get_value_from(entry, 'published', '') + ')'
    summary = get_value_from(entry, 'summary', '')
    link = get_value_from(entry, ['link', 'id'], '')

    tags = None
    if tagcontent is not None and link is not '':
        if delay:
            time.sleep(random.randint(2, 4))
        delay = True
        thing = urllib.request.urlopen(link).read().decode()
        if re.search(tagcontent, thing) is not None:
            # Note that tags will be [] if the regex matches but has no groups
            tags = re.findall(tagcontent, thing)
            if tags is not None and len(tags) is not 0:
                print("Tags: " + ', '.join(tags))
    if skipuntagged and tags is None:
        set_ignored(db, guid)
        continue

    print('{} {}\n{}\n{}\n\n'.format(title, published, summary, link))

    if not dry_run:
        set_read(db, guid, tags)

    if just_one:
        break

        
close_connection(db)
