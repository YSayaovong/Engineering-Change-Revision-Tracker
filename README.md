# Engineering Change & Revision Tracker

SQLite-backed engineering change request simulator with controlled state transitions and append-only event history.

## Workflow
`DRAFT → SUBMITTED → IN_REVIEW → APPROVED → RELEASED`. Requests may also be rejected from SUBMITTED or IN_REVIEW.

## Run
```bash
pip install -r requirements.txt
python src/tracker.py --db data/demo.sqlite create --part CORE-100 --from-rev A --to-rev B --description "Correct drawing note" --actor designer
python src/tracker.py --db data/demo.sqlite transition --id 1 --status SUBMITTED --actor designer
python src/tracker.py --db data/demo.sqlite list
python src/tracker.py --db data/demo.sqlite history --id 1
pytest -q
```

Stores change request part, revisions, description, status, and timestamped actor-labeled transitions.

**Limitations:** Synthetic demo; no authentication, real approval signatures, role-based authorization, attachments, or enterprise SAP/Creo/PLM integration. Not a compliance-grade audit system.
