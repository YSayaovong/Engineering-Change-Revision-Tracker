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

## How to measure the workflow

Measure elapsed time from SUBMITTED to APPROVED for approved requests, plus the age of currently open requests in each status. Report the median and 90th percentile with request counts for a defined submission cohort. Track rejection rate separately to help interpret a change in approval time. The prototype records UTC timestamps. A meaningful baseline needs a synthetic dataset with realistic intervals or approved shareable historical data.
