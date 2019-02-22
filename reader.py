#!/usr/bin/env python3

import sqlite3
import sys
import feedparser
from pprint import pprint

db_name = 'rss.db'
url = sys.argv[1]

def open_connection():
    return sqlite3.connect(db_name)
def close_connection(db):
    db.commit()
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

db_init()
db = open_connection()
d = feedparser.parse(url)
for entry in d['entries']:
    guid = entry['link']
    if is_read(db, guid):
        continue
    print('{} ({})\n{}\n{}\n\n'.format(entry['title'], entry['published'], entry['summary'], entry['link']))
    set_read(db, guid)

        
close_connection(db)
