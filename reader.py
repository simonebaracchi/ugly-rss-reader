#!/usr/bin/env python3

import sqlite3
import sys
import os
import time
import feedparser
from pprint import pprint

os.chdir(os.path.dirname(os.path.abspath(__file__)))
db_name = 'rss.db'
debug = False
just_one = False
dry_run = False
days = None
url = None

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

def db_init():
    db = open_connection()
    try:
        c = db.cursor()
        if not table_exists(db, 'Stock'):
            c.execute('''CREATE TABLE IF NOT EXISTS RSS (guid text primary key)''')
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
    
def set_read(db, guid):
    c = db.cursor()
    query = c.execute('''INSERT OR REPLACE INTO RSS(guid) VALUES (?)''', (guid,))
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
    else:
        url = arg
if url == None:
    print('No URL specified, exiting.')
    sys.exit(1)

db_init()
db = open_connection()
d = feedparser.parse(url)

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
    
    title = get_value_from(entry, 'title', '')
    published = '(' + get_value_from(entry, 'published', '') + ')'
    summary = get_value_from(entry, 'summary', '')
    link = get_value_from(entry, ['link', 'id'], '')

    print('{} {}\n{}\n{}\n\n'.format(title, published, summary, link))

    if not dry_run:
        set_read(db, guid)

    if just_one:
        break
        
close_connection(db)
