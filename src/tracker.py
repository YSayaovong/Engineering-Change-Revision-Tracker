"""SQLite engineering change request tracker with controlled transitions."""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ALLOWED={'DRAFT':{'SUBMITTED'},'SUBMITTED':{'IN_REVIEW','REJECTED'},'IN_REVIEW':{'APPROVED','REJECTED'},'APPROVED':{'RELEASED'},'REJECTED':set(),'RELEASED':set()}

def connect(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path);db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript("""CREATE TABLE IF NOT EXISTS changes (id INTEGER PRIMARY KEY, part_number TEXT NOT NULL, from_rev TEXT NOT NULL, to_rev TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'DRAFT'); CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, change_id INTEGER NOT NULL REFERENCES changes(id), from_status TEXT, to_status TEXT NOT NULL, actor TEXT NOT NULL, timestamp TEXT NOT NULL);""")
    return db

def stamp():return datetime.now(timezone.utc).isoformat()

def create(db,part,from_rev,to_rev,description,actor):
    if not all((part.strip(),from_rev.strip(),to_rev.strip(),description.strip(),actor.strip())):raise ValueError('All fields are required')
    if from_rev==to_rev:raise ValueError('Revision must change')
    with db:
        cur=db.execute('INSERT INTO changes(part_number,from_rev,to_rev,description) VALUES(?,?,?,?)',(part,from_rev,to_rev,description))
        db.execute('INSERT INTO history(change_id,from_status,to_status,actor,timestamp) VALUES(?,?,?,?,?)',(cur.lastrowid,None,'DRAFT',actor,stamp()))
    return cur.lastrowid

def transition(db,change_id,status,actor):
    row=db.execute('SELECT status FROM changes WHERE id=?',(change_id,)).fetchone()
    if row is None:raise ValueError('Change request not found')
    current=row['status'];status=status.upper()
    if status not in ALLOWED[current]:raise ValueError(f'Invalid transition {current} -> {status}')
    if not actor.strip():raise ValueError('Actor required')
    with db:
        db.execute('UPDATE changes SET status=? WHERE id=?',(status,change_id))
        db.execute('INSERT INTO history(change_id,from_status,to_status,actor,timestamp) VALUES(?,?,?,?,?)',(change_id,current,status,actor,stamp()))

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/changes.sqlite');sub=p.add_subparsers(dest='action',required=True)
    c=sub.add_parser('create');c.add_argument('--part',required=True);c.add_argument('--from-rev',required=True);c.add_argument('--to-rev',required=True);c.add_argument('--description',required=True);c.add_argument('--actor',required=True)
    t=sub.add_parser('transition');t.add_argument('--id',type=int,required=True);t.add_argument('--status',required=True,choices=['SUBMITTED','IN_REVIEW','APPROVED','REJECTED','RELEASED']);t.add_argument('--actor',required=True)
    sub.add_parser('list');h=sub.add_parser('history');h.add_argument('--id',type=int,required=True)
    a=p.parse_args();db=connect(a.db)
    if a.action=='create':print('Created change:',create(db,a.part,a.from_rev,a.to_rev,a.description,a.actor))
    elif a.action=='transition':transition(db,a.id,a.status,a.actor);print('Updated:',a.id,a.status)
    elif a.action=='list':
        for row in db.execute('SELECT * FROM changes ORDER BY id'):print(dict(row))
    elif a.action=='history':
        for row in db.execute('SELECT * FROM history WHERE change_id=? ORDER BY id',(a.id,)):print(dict(row))
if __name__=='__main__':main()
