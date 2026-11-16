# Engineering change workflow case study

## Business problem

A manufacturing team needs to know which revision is ready to release and which changes are still waiting for review. This synthetic case study models how a revision request moves from draft to release using the included SQLite tracker.

## Stakeholders and requirements

| Stakeholder | Need | What the prototype demonstrates |
| --- | --- | --- |
| Engineering requester | Identify the part, previous revision, proposed revision, and reason for change | Create a request with required fields and record its initial DRAFT event |
| Engineering reviewer | Move submitted requests into review and record an approval or rejection | Validate allowed status transitions and log each accepted change |
| Manufacturing coordinator | Identify changes that have been released | Expose current status in the list and show a chronological history for each request |

## Acceptance scenarios

| Given | When | Expected result |
| --- | --- | --- |
| A request for CORE-100 with revision A changing to B | A requester submits it, a reviewer moves it through review and approval, and a coordinator releases it | Status is RELEASED and history shows DRAFT, SUBMITTED, IN_REVIEW, APPROVED, and RELEASED |
| A request is IN_REVIEW | Someone attempts to release it directly | The transition is rejected and status stays IN_REVIEW |
| A request is SUBMITTED | A reviewer rejects it and someone tries to reopen it | Status stays REJECTED and the rejected reopening adds no history row |
| Both revisions are A | A requester saves the draft | Validation rejects the request |

Run the tracker commands described in the [README](../README.md) against an empty demo database. The scenarios are written for user acceptance testing. Actor labels record what the operator entered. Production approval would require verified identities, permissions, and stronger audit controls.

## Where the workflow slows down

Run `python src/stage_metrics_demo.py` from the repository root. It builds a temporary SQLite database with five synthetic requests and runs the [stage metrics query](../sql/stage_metrics.sql) as of October 15, 2026 (UTC).

| Stage | Completed visits | Mean completed days | Open visits | Oldest open days |
| --- | ---: | ---: | ---: | ---: |
| Submitted | 4 | 1.8 | 1 | 5.0 |
| In review | 2 | 7.0 | 1 | 10.0 |
| Approved | 2 | 1.5 | 0 | — |

A visit starts when a request enters a stage and ends at the next transition. A rejection closes the current stage and counts as a completed visit. Open visits are aged separately as of the report timestamp so in-progress work remains visible. Draft and terminal statuses are outside this stage report.

**Recommendation:** Review the 10-day open request with the engineering review owner, then check whether reviewer availability or missing information explains the queue. The sample points to a stage worth investigating. It has two completed review visits, so it supports a demonstration of the method. With a larger dataset, report median and 90th-percentile review time by submission cohort and track rejection rate separately.
