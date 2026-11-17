# Engineering Change & Revision Tracker

**Engineering change control | Revision traceability | Workflow simulation**

A SQLite-backed command-line simulator demonstrating how engineering change requests move through defined review states. All examples are **synthetic**.

## Business problem
Engineering revisions need clear status, traceability and handoffs. This project models a controlled request lifecycle and stores an append-only history of actor-labeled transitions.

## Workflow
```text
DRAFT → SUBMITTED → IN_REVIEW → APPROVED → RELEASED
             ↘ REJECTED ↗
```
Rejection is supported from **SUBMITTED** or **IN_REVIEW**; the diagram is conceptual, not an exhaustive transition specification.

## Try the demo
```bash
python -m pip install -r requirements.txt
python src/tracker.py --db data/demo.sqlite create --part CORE-100 --from-rev A --to-rev B --description "Correct drawing note" --actor designer
python src/tracker.py --db data/demo.sqlite transition --id 1 --status SUBMITTED --actor designer
python src/tracker.py --db data/demo.sqlite list
python src/tracker.py --db data/demo.sqlite history --id 1
pytest -q
```

## Evidence and analyst skills
- Records part identifier, original and proposed revisions, description and status
- Applies controlled state transitions
- Retains timestamped, actor-labeled transition history
- Demonstrates SQLite-backed workflow data and testable business rules

## How a business user would evaluate it
Review the request status and transition history; check whether the workflow prevents invalid transitions; identify which additional fields, approvals and controls a real change-management system would require.

## Scope and limitations
This is **not** an enterprise PLM system. There is no authentication, validated electronic signature, role-based authorization, attachment handling or integration with SAP, Creo or Windchill. Actor labels are user-provided, not authenticated identities. The event history is a demo record, **not a compliance-grade audit trail**.

**Relevant roles:** Engineering Change Analyst, Configuration Analyst, PLM/Engineering Systems Analyst.

[Related BOM validation project](https://github.com/YSayaovong/Engineering-BOM-Validation-System) · [Portfolio website repository](https://github.com/YSayaovong/operations-analytics-portfolio)
