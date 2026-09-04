# Planning evidence

Record the review trail that turns the neutral implementation brief into an
approved execution plan. The active main planning lane or a dedicated Planner
may own the initial draft; a Planner subagent is not required unless the
selected workflow explicitly routes the draft to one.

## Machine-verifiable Ralplan handoff

When Ralplan is selected, keep the marker-bounded YAML block intact and
populate it from the actual native task surface and
`.omx/state/session.json` plus `.omx/state/subagent-tracking.json`; do not infer
or fabricate role, leader, session, or thread identity. Record SHA-256 digests
from the approved PRD and test-spec bytes, and refresh them after every plan
revision. From the installed `zero-to-hero` skill directory, run:

```bash
python scripts/planning_evidence_check.py /path/to/target-repo --mode project
```

before handing a Ralplan plan to Ultragoal, Team, Ralph, Autopilot, Pipeline,
or an implementation lane. The source template intentionally remains `pending`
and passes only `--mode template`; a generated project that selects Ralplan
must remain blocked until `--mode project` passes. A non-Ralplan path keeps
this block pending and records its separate approval evidence below; it must
never claim Ralplan consensus.

<!-- RALPLAN_EVIDENCE:START -->
```yaml
schema_version: 1
evidence_status: pending
review_cycle: 0
planning_artifacts:
  draft_owner: pending
  prd_path: "<populate with a repository-relative PRD path>"
  prd_sha256: "<pending>"
  test_spec_path: "<populate with a repository-relative test-spec path>"
  test_spec_sha256: "<pending>"
role_routing:
  status: pending
  surface: pending
  documented_leader_proof: false
  blocked_reason: evidence_not_yet_recorded
ralplan_consensus_gate:
  required: true
  sequence:
    - architect-review
    - critic-review
  planning_artifacts_are_not_consensus: true
  required_review_roles:
    - architect
    - critic
  ralplan_architect_review:
    agent_role: architect
    provenance_kind: native_subagent
    verdict: pending
    review_cycle: 0
    completed_at: "<pending>"
    session_id: "<pending>"
    thread_id: "<pending>"
    tracker_path: .omx/state/subagent-tracking.json
  ralplan_critic_review:
    agent_role: critic
    provenance_kind: native_subagent
    verdict: pending
    review_cycle: 0
    completed_at: "<pending>"
    session_id: "<pending>"
    thread_id: "<pending>"
    tracker_path: .omx/state/subagent-tracking.json
  complete: false
  blocked_reason: evidence_not_yet_recorded
```
<!-- RALPLAN_EVIDENCE:END -->

When the native task surface exposes typed `agent_type` routing, record
`role_routing.status: available`, `surface: native_agent_type`, and
`documented_leader_proof: true`. When it reports
`role_routing_unavailable`, run `omx ralplan preflight --json`. If that returns
`unsupported_documented_leader_proof`, record the blocker and stop: prompt
labels, transcript state, session IDs, thread IDs, working directories, and
artifact-only reviews do not prove a native Ralplan lane.

The Architect and Critic must be separate, sequential native subagents in the
current `.omx/state/session.json` session. The Architect tracker thread must be
completed before the Critic thread's `first_seen_at` or `started_at`, and both
threads must be completed. Use timezone-bearing RFC 3339 timestamps. Set the
top-level `review_cycle` to the OMX candidate cycle and carry that exact value
on both nested reviews. OMX 0.20.3's initial standalone Ralplan seed omits
`review_cycle`; only that non-return initial state binds to cycle `0`. When
mode state is returning to Ralplan, the candidate cycle must be explicit and
strictly greater than the recorded parent cycle; if mode state already
persists an advanced candidate cycle, match it exactly. An older review pair
never approves a newer cycle. Only `verdict: approve` counts. `codex_exec`,
`omx_adapted`, leader self-review, reused threads, stale artifact hashes,
non-approving reviews, or missing session/tracker evidence leave
`ralplan_consensus_gate.complete: false`.

## Planner draft

- Date:
- Draft owner: `main` or `planner`
- Plan artifact: `docs/implementation/EXECPLAN.md` (draft; review pending)
- Milestones:
- Risks and assumptions:

## Architect review

- Date:
- Native subagent thread:
- Architecture invariants checked:
- Boundary or dependency concerns:
- Required revisions:

## Critic review

Run only after the Architect review has completed.

- Date:
- Native subagent thread:
- Failure modes challenged:
- Validation gaps:
- Required revisions:

## Explicit consensus gate

- Status: `pending`
- Approved brief revision:
- Approved plan revision:
- Remaining non-blocking risks:

When Ralplan is selected, execution must not begin until the
machine-verifiable gate is complete. Every execution path must also resolve or
explicitly accept each blocking Architect or Critic item under its selected
planning contract.

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
