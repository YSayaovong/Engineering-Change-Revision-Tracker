import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tracker import connect,create,transition

def test_workflow(tmp_path):
    db=connect(tmp_path/'t.sqlite');id=create(db,'PART-1','A','B','Correct specification','designer')
    for status in ['SUBMITTED','IN_REVIEW','APPROVED','RELEASED']:transition(db,id,status,'reviewer')
    assert db.execute('SELECT status FROM changes WHERE id=?',(id,)).fetchone()['status']=='RELEASED'
    assert db.execute('SELECT count(*) FROM history WHERE change_id=?',(id,)).fetchone()[0]==5
    with pytest.raises(ValueError):transition(db,id,'SUBMITTED','reviewer')

def test_revision_guard(tmp_path):
    db=connect(tmp_path/'t.sqlite')
    with pytest.raises(ValueError):create(db,'X','A','A','bad','tester')
