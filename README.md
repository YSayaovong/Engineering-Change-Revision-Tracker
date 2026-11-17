# Engineering Change & Revision Tracker

**Engineering change control · Revision traceability · Workflow validation · SQLite**

## Project overview

The Engineering Change & Revision Tracker is a Python command-line application that simulates a structured engineering change request lifecycle. It records proposed part revisions, enforces defined workflow transitions, and stores timestamped status history in a SQLite database.

Engineering changes require consistent identification of the affected part, the current and proposed revisions, a documented reason for the change, and visibility into the request's progression. This project demonstrates how a small, rule-driven system can make those records consistent and prevent requests from bypassing the configured sequence of workflow states.

The application uses synthetic demonstration records and does not connect to production engineering systems.

## Change request lifecycle

```text
DRAFT → SUBMITTED → IN_REVIEW → APPROVED → RELEASED
             ↘ REJECTED ↙
```

The diagram summarizes the process. In the implemented rules, **REJECTED** is reachable from either **SUBMITTED** or **IN_REVIEW**. Rejected and released requests are terminal; there is no resubmission or reopening workflow.

| Current status | Allowed next status |
|---|---|
| `DRAFT` | `SUBMITTED` |
| `SUBMITTED` | `IN_REVIEW`, `REJECTED` |
| `IN_REVIEW` | `APPROVED`, `REJECTED` |
| `APPROVED` | `RELEASED` |
| `REJECTED` | None |
| `RELEASED` | None |

Invalid transitions raise an error and are not recorded as completed changes.

## How the application works

1. **Register a proposed change.** Create a request with a part number, existing revision, proposed revision, description, and actor label.
2. **Validate the request.** Reject blank required values and requests where the original and proposed revision strings are equal.
3. **Initialize the workflow.** Store the request in `DRAFT` status and create its initial history entry.
4. **Advance the request.** Apply an authorized-by-rule status transition; the current state determines which next states are permitted.
5. **Record the transition.** Update the request's current status and insert a history entry containing the previous state, new state, actor label, and UTC timestamp.
6. **Inspect records.** List current requests or retrieve the recorded status history for an individual request.

The workflow rules validate **state order**, not the real-world identity or authority of the person initiating a transition. Input strings are trimmed, and invalid requests produce a nonzero command exit status without recording a completed workflow event.

## Data model

SQLite stores information in two related tables:

| Table | Purpose | Stored information |
|---|---|---|
| `changes` | Current request record | Request ID, part number, original revision, proposed revision, description, current status |
| `history` | Recorded lifecycle events | Event ID, request ID, previous status, new status, actor label, UTC timestamp |

The `history.change_id` field references `changes.id` through a foreign key. Database writes for request creation and status changes are grouped using SQLite transactions.

History entries are inserted as the application performs transitions. The application itself does not provide a command to edit or delete history entries; however, the database does not enforce a tamper-proof or compliance-grade audit record.

## Running the demonstration

The project requires Python. `pytest` is used for automated tests.

```bash
python -m pip install -r requirements.txt

python src/tracker.py --db data/demo.sqlite create --part CORE-100 --from-rev A --to-rev B --description "Correct drawing note" --actor designer

python src/tracker.py --db data/demo.sqlite transition --id 1 --status SUBMITTED --actor designer

python src/tracker.py --db data/demo.sqlite transition --id 1 --status IN_REVIEW --actor reviewer

python src/tracker.py --db data/demo.sqlite list
python src/tracker.py --db data/demo.sqlite history --id 1

python -m pytest -v
```

The examples assume a new demonstration database, where the first created request receives ID `1`. Re-running them against an existing database may create a different request ID or encounter an invalid transition.

### Available commands

- `create`: Registers a proposed part revision and initializes its history.
- `transition`: Changes a request status when the move is permitted by the workflow rules.
- `list`: Displays current request records.
- `history`: Displays the recorded transitions associated with a request.

## Automated validation

The automated test suite covers:

- The complete `DRAFT` → `RELEASED` lifecycle and ordered history events.
- Both rejection routes and terminal-state protection.
- Invalid revision changes, missing mandatory fields, whitespace normalization, and skipped states.
- Missing request IDs and invalid actor labels without unintended history entries.
- SQLite foreign-key enforcement and persistence across database connections.
- CLI operations, error exit codes, and execution from a different working directory.

GitHub Actions runs the test suite automatically on pushes, pull requests, and manual dispatch. The actor labels and status history remain a demonstration, not verified approval evidence.

## Engineering configuration relevance

The application demonstrates several foundational engineering configuration and change-management concepts:

- **Change identification:** Each request identifies an affected part and its proposed revision movement.
- **Revision traceability:** The request maintains a record of its original and proposed revision values.
- **Process consistency:** A defined transition map prevents progression through unsupported workflow states.
- **Configuration status visibility:** The current status can be retrieved alongside the request's identifying information.
- **Change history:** Stored transition records allow the simulated request's progress to be reviewed.
- **Business-rule validation:** Automated checks and tests provide a reproducible example of workflow controls.

The application models **request-status progression**. It does not confirm that any engineering drawing, CAD model, BOM, or released product configuration was actually revised.

## Repository structure

```text
src/tracker.py           Command-line application, state rules, and SQLite operations
tests/test_tracker.py    Automated workflow and revision-validation tests
requirements.txt         Test dependency
.github/workflows/tests.yml  Automated GitHub Actions tests
.gitignore               Excludes local databases and Python caches
README.md                Project documentation
```

## Scope and limitations

This is a local engineering change workflow simulator, not an enterprise PLM or production release-management system.

- No integration with Creo, Windchill, SAP, or other CAD/PLM/ERP platforms.
- No authentication, identity verification, role-based access control, or approval authority validation.
- Actor names are user-entered labels, not verified identities or electronic signatures.
- No attachments, drawing revision processing, engineering BOM updates, or actual product release.
- No change impact assessment, effectivity control, baseline comparison, or configuration audit process.
- No automated notifications, escalation rules, or multi-user coordination features.
- Event records are informative demonstration data, **not** a compliance-grade or tamper-resistant audit trail.
- Rejected and released requests cannot be reopened through the current application commands.

## Future development opportunities

Potential extensions include role-based approval simulation, change-impact evaluation across affected assemblies, approved baseline comparison, engineering BOM revision linkage, exception reporting, and configuration status dashboards. These are future possibilities and are **not implemented** in the current project.

## Related projects

[Creo CAD Configuration Validation Toolkit](https://github.com/YSayaovong/Creo-CAD-Application-Support-Toolkit) · [Engineering BOM Validation System](https://github.com/YSayaovong/Engineering-BOM-Validation-System)

## Public portfolio usage

This repository is an independently developed **synthetic-data simulation** intended to demonstrate engineering configuration and change-management concepts. Use a fresh, local SQLite database for the examples. No company configuration, drawing, BOM, or engineering release is read or changed.

The sample commands create an illustrative workflow; they do **not** constitute a real engineering change approval or configuration release. This project does not assert verified professional deployment or integration with any employer system.
