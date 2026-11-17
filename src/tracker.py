"""SQLite-backed synthetic engineering change and revision workflow simulator.

Workflow rules demonstrate status control only; actor labels are not authenticated
identities and the records are not an approved engineering change audit trail.
"""
import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ALLOWED = {
    'DRAFT': {'SUBMITTED'},
    'SUBMITTED': {'IN_REVIEW', 'REJECTED'},
    'IN_REVIEW': {'APPROVED', 'REJECTED'},
    'APPROVED': {'RELEASED'},
    'REJECTED': set(),
    'RELEASED': set(),
}


def connect(path):
    """Open a local database and initialize two simple linked tables."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript("""
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY,
            part_number TEXT NOT NULL,
            from_rev TEXT NOT NULL,
            to_rev TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'DRAFT'
        );
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY,
            change_id INTEGER NOT NULL REFERENCES changes(id),
            from_status TEXT,
            to_status TEXT NOT NULL,
            actor TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
    """)
    return db


def stamp():
    return datetime.now(timezone.utc).isoformat()


def required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} is required')
    return value.strip()


def create(db, part, from_rev, to_rev, description, actor):
    """Create a DRAFT request and its initial history entry atomically."""
    part = required(part, 'Part number')
    from_rev = required(from_rev, 'Original revision')
    to_rev = required(to_rev, 'Proposed revision')
    description = required(description, 'Description')
    actor = required(actor, 'Actor')
    if from_rev == to_rev:
        raise ValueError('Revision must change')
    with db:
        cur = db.execute(
            'INSERT INTO changes(part_number,from_rev,to_rev,description) '
            'VALUES(?,?,?,?)', (part, from_rev, to_rev, description)
        )
        db.execute(
            'INSERT INTO history(change_id,from_status,to_status,actor,timestamp) '
            'VALUES(?,?,?,?,?)', (cur.lastrowid, None, 'DRAFT', actor, stamp())
        )
    return cur.lastrowid


def transition(db, change_id, status, actor):
    """Validate and record one status transition in a single transaction."""
    actor = required(actor, 'Actor')
    status = required(status, 'Status').upper()
    with db:
        row = db.execute(
            'SELECT status FROM changes WHERE id=?', (change_id,)
        ).fetchone()
        if row is None:
            raise ValueError('Change request not found')
        current = row['status']
        if current not in ALLOWED:
            raise ValueError(f'Unknown stored status: {current}')
        if status not in ALLOWED[current]:
            raise ValueError(f'Invalid transition {current} -> {status}')
        cur = db.execute(
            'UPDATE changes SET status=? WHERE id=? AND status=?',
            (status, change_id, current)
        )
        if cur.rowcount != 1:
            raise ValueError('Change status changed before update; retry')
        db.execute(
            'INSERT INTO history(change_id,from_status,to_status,actor,timestamp) '
            'VALUES(?,?,?,?,?)', (change_id, current, status, actor, stamp())
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Track synthetic part-revision change requests using SQLite.'
    )
    parser.add_argument(
        '--db', type=Path, default=Path('data/changes.sqlite'),
        help='Local SQLite database path (default: data/changes.sqlite).'
    )
    sub = parser.add_subparsers(dest='action', required=True)
    create_cmd = sub.add_parser('create', help='Register a draft change request.')
    create_cmd.add_argument('--part', required=True)
    create_cmd.add_argument('--from-rev', required=True)
    create_cmd.add_argument('--to-rev', required=True)
    create_cmd.add_argument('--description', required=True)
    create_cmd.add_argument('--actor', required=True)
    transition_cmd = sub.add_parser('transition', help='Advance a request state.')
    transition_cmd.add_argument('--id', type=int, required=True)
    transition_cmd.add_argument(
        '--status', required=True,
        choices=['SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'RELEASED']
    )
    transition_cmd.add_argument('--actor', required=True)
    sub.add_parser('list', help='Show current change requests.')
    history_cmd = sub.add_parser('history', help='Show status history.')
    history_cmd.add_argument('--id', type=int, required=True)
    args = parser.parse_args(argv)

    try:
        db = connect(args.db)
        try:
            if args.action == 'create':
                change_id = create(
                    db, args.part, args.from_rev, args.to_rev,
                    args.description, args.actor
                )
                print(f'Created change: {change_id}')
            elif args.action == 'transition':
                transition(db, args.id, args.status, args.actor)
                print(f'Updated: {args.id} {args.status}')
            elif args.action == 'list':
                for row in db.execute('SELECT * FROM changes ORDER BY id'):
                    print(dict(row))
            elif args.action == 'history':
                rows = db.execute(
                    'SELECT * FROM history WHERE change_id=? ORDER BY id',
                    (args.id,)
                ).fetchall()
                if not rows:
                    existing = db.execute(
                        'SELECT 1 FROM changes WHERE id=?', (args.id,)
                    ).fetchone()
                    if existing is None:
                        raise ValueError('Change request not found')
                for row in rows:
                    print(dict(row))
        finally:
            db.close()
    except (ValueError, sqlite3.Error, OSError) as exc:
        print(f'Tracker error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
