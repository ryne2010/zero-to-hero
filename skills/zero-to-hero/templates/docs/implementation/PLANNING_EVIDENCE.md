# Planning evidence

Record the review trail that turns the neutral implementation brief into an
approved execution plan.

## Planner draft

- Date:
- Plan artifact:
- Milestones:
- Risks and assumptions:

## Architect review

- Date:
- Architecture invariants checked:
- Boundary or dependency concerns:
- Required revisions:

## Critic review

Run after the Architect review.

- Date:
- Failure modes challenged:
- Validation gaps:
- Required revisions:

## Explicit consensus gate

- Status: `pending`
- Approved brief revision:
- Approved plan revision:
- Participants or authority:
- Remaining non-blocking risks:

Execution must not begin until the status is `approved` and every blocking
Architect or Critic item is resolved or explicitly accepted.

## Execution selection

- Selected path: `native-codex`, `deterministic-sequential`, `omx-ultragoal`, or
  explicitly chosen `ralph-alternate`
- Tool/version probe:
- Reason:
- Parallel work boundaries:

OMX Team is conditional on a supported environment and disjoint ownership.
Ultragoal state is leader-owned; workers return evidence and never edit or
checkpoint the leader ledger. Ralph is an alternate single-owner execution
loop, never a mandatory post-Ultragoal review phase.

## Independent completion reviews

- Code review evidence:
- Architecture-invariant review evidence:
- UltraQA or applicable final product verification:
- Authoritative done-command result:
