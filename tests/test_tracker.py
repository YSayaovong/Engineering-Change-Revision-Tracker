"""Regression tests for the synthetic engineering change workflow."""
import ast
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from tracker import connect, create, main, transition


@pytest.fixture
def db(tmp_path):
    conn = connect(tmp_path / 'change-tracker.sqlite')
    yield conn
    conn.close()


def test_full_workflow_records_history(db):
    change_id = create(db, 'PART-1', 'A', 'B', 'Correct specification', 'designer')
    for status in ['SUBMITTED', 'IN_REVIEW', 'APPROVED', 'RELEASED']:
        transition(db, change_id, status, 'reviewer')
    row = db.execute('SELECT * FROM changes WHERE id=?', (change_id,)).fetchone()
    assert row['status'] == 'RELEASED'
    events = db.execute(
        'SELECT * FROM history WHERE change_id=? ORDER BY id', (change_id,)
    ).fetchall()
    assert [event['to_status'] for event in events] == [
        'DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'RELEASED'
    ]
    assert [event['from_status'] for event in events] == [
        None, 'DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED'
    ]
    assert all(event['actor'] for event in events)
    assert all(datetime.fromisoformat(event['timestamp']).tzinfo for event in events)


@pytest.mark.parametrize('from_status,reject', [
    ('SUBMITTED', 'REJECTED'), ('IN_REVIEW', 'REJECTED')
])
def test_rejection_routes_are_terminal(db, from_status, reject):
    change_id = create(db, 'PART-2', 'A', 'B', 'Change note', 'designer')
    transition(db, change_id, 'SUBMITTED', 'designer')
    if from_status == 'IN_REVIEW':
        transition(db, change_id, 'IN_REVIEW', 'reviewer')
    transition(db, change_id, reject, 'reviewer')
    with pytest.raises(ValueError, match='Invalid transition'):
        transition(db, change_id, 'SUBMITTED', 'reviewer')


@pytest.mark.parametrize('original,proposed', [
    ('A', 'A'), (' A ', 'A'), ('', 'B'), ('A', ' '),
])
def test_invalid_revision_create(db, original, proposed):
    with pytest.raises(ValueError):
        create(db, 'PART-1', original, proposed, 'Reason', 'designer')
    assert db.execute('SELECT COUNT(*) FROM changes').fetchone()[0] == 0
    assert db.execute('SELECT COUNT(*) FROM history').fetchone()[0] == 0


@pytest.mark.parametrize('field', ['part', 'description', 'actor'])
def test_missing_required_fields(db, field):
    kwargs = dict(part='PART-1', from_rev='A', to_rev='B',
                  description='Valid reason', actor='designer')
    kwargs[field] = '  '
    with pytest.raises(ValueError, match='required'):
        create(db, **kwargs)


@pytest.mark.parametrize('current_path,target', [
    ([], 'APPROVED'),
    (['SUBMITTED'], 'RELEASED'),
    (['SUBMITTED', 'IN_REVIEW'], 'RELEASED'),
])
def test_skipped_transitions_do_not_mutate(db, current_path, target):
    change_id = create(db, 'PART-1', 'A', 'B', 'Change note', 'designer')
    for status in current_path:
        transition(db, change_id, status, 'designer')
    before = db.execute(
        'SELECT COUNT(*) FROM history WHERE change_id=?', (change_id,)
    ).fetchone()[0]
    with pytest.raises(ValueError, match='Invalid transition'):
        transition(db, change_id, target, 'reviewer')
    after = db.execute(
        'SELECT COUNT(*) FROM history WHERE change_id=?', (change_id,)
    ).fetchone()[0]
    assert before == after


def test_released_is_terminal(db):
    change_id = create(db, 'PART-1', 'A', 'B', 'Change note', 'designer')
    for status in ['SUBMITTED', 'IN_REVIEW', 'APPROVED', 'RELEASED']:
        transition(db, change_id, status, 'reviewer')
    with pytest.raises(ValueError):
        transition(db, change_id, 'SUBMITTED', 'reviewer')
    assert db.execute('SELECT COUNT(*) FROM history').fetchone()[0] == 5


def test_missing_change_rejected(db):
    with pytest.raises(ValueError, match='not found'):
        transition(db, 999, 'SUBMITTED', 'reviewer')


def test_blank_actor_rejected_without_history(db):
    change_id = create(db, 'PART-1', 'A', 'B', 'Change note', 'designer')
    with pytest.raises(ValueError, match='Actor is required'):
        transition(db, change_id, 'SUBMITTED', '  ')
    assert db.execute('SELECT status FROM changes').fetchone()['status'] == 'DRAFT'
    assert db.execute('SELECT COUNT(*) FROM history').fetchone()[0] == 1


def test_input_is_trimmed(db):
    change_id = create(db, ' PART-1 ', ' A ', ' B ', ' Reason ', ' designer ')
    row = db.execute('SELECT * FROM changes WHERE id=?', (change_id,)).fetchone()
    assert (row['part_number'], row['from_rev'], row['to_rev'], row['description']) == (
        'PART-1', 'A', 'B', 'Reason'
    )
    assert db.execute('SELECT actor FROM history').fetchone()['actor'] == 'designer'


def test_foreign_key_integrity(db):
    assert db.execute('PRAGMA foreign_keys').fetchone()[0] == 1


def test_persistence_across_connections(tmp_path):
    path = tmp_path / 'tracker.sqlite'
    first = connect(path)
    change_id = create(first, 'PART-1', 'A', 'B', 'Change note', 'designer')
    first.close()
    second = connect(path)
    try:
        assert second.execute(
            'SELECT status FROM changes WHERE id=?', (change_id,)
        ).fetchone()['status'] == 'DRAFT'
    finally:
        second.close()


def test_cli_success(tmp_path, capsys):
    path = tmp_path / 'cli.sqlite'
    assert main(['--db', str(path), 'create', '--part', 'PART-1',
                 '--from-rev', 'A', '--to-rev', 'B',
                 '--description', 'Reason', '--actor', 'designer']) == 0
    assert main(['--db', str(path), 'transition', '--id', '1',
                 '--status', 'SUBMITTED', '--actor', 'designer']) == 0
    assert main(['--db', str(path), 'list']) == 0
    assert main(['--db', str(path), 'history', '--id', '1']) == 0
    out = capsys.readouterr().out
    assert 'Created change: 1' in out
    assert 'SUBMITTED' in out


def test_cli_failure_has_nonzero_exit(tmp_path, capsys):
    path = tmp_path / 'cli.sqlite'
    assert main(['--db', str(path), 'transition', '--id', '42',
                 '--status', 'SUBMITTED', '--actor', 'designer']) == 1
    assert 'not found' in capsys.readouterr().err


def test_cli_missing_history_id_nonzero(tmp_path, capsys):
    path = tmp_path / 'cli.sqlite'
    assert main(['--db', str(path), 'history', '--id', '42']) == 1
    assert 'not found' in capsys.readouterr().err


def test_command_from_other_directory(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / 'src' / 'tracker.py'),
         '--db', str(tmp_path / 'subdir' / 'tracker.sqlite'),
         'create', '--part', 'PART-1', '--from-rev', 'A', '--to-rev', 'B',
         '--description', 'Reason', '--actor', 'designer'],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'subdir' / 'tracker.sqlite').is_file()
