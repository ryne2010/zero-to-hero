# Neutral implementation brief

This is the execution-neutral handoff. It remains authoritative whether work is
run with native Codex planning and subagents, deterministic sequential
execution, or a compatible OMX adapter.

## Approved outcome

- Product outcome: implement only the outcome recorded in the canonical
  requirements and source-of-truth map for the selected profiles.
- Primary users and jobs: use the approved product requirements; an absent user
  or job definition is a planning blocker, not permission to invent one.
- Observable success: the target-specific behaviors pass the exact checks in
  `AGENTS.md`, with evidence linked from `FINAL_HANDOFF.md`.
- Explicit non-goals: do not expand scope, replace product decisions, bypass
  permission gates, or treat this scaffold as runtime implementation.

## Selected capability and profile evidence

| Capability | Profile | Authority | Evidence |
| --- | --- | --- | --- |
| Selected capabilities | Selected profiles | user-approved and/or repository-evidenced | canonical generated-file manifest and source-of-truth map |

## Scope and invariants

- In scope: the selected profiles and their canonical requirements.
- Out of scope: unselected profiles, undocumented features, and all work
  prohibited by repository instructions.
- Architectural invariants: preserve the boundaries recorded in canonical
  requirements, `AGENTS.md`, and the source-of-truth map.
- Compatibility boundaries: do not change declared public formats, platforms,
  protocols, or dependency contracts without an approved decision.
- Privacy and security boundaries: minimize data, preserve trust separation,
  and never expose credentials or private production data.
- External-effect and permission boundaries: local inert validation is allowed;
  production changes and physical effects require separate explicit authority.

## Canonical inputs

- Source-of-truth map: `docs/00-meta/source-of-truth-map.yaml`
- Decision ledger: `docs/00-meta/decision-ledger.yaml`
- Agent context: `docs/AGENT_CONTEXT.md`
- Durable plan contract: `PLANS.md`
- Profile-specific contracts: every selected profile requirement linked by
  `docs/00-meta/source-of-truth-map.yaml`.

## Ordered implementation stories

| ID | User-visible result | Dependencies | Validation | Owner |
| --- | --- | --- | --- | --- |
| STORY-001 | First approved milestone from the durable plan | canonical requirements and resolved blockers | targeted checks plus the authoritative done command | leader |

## Validation and evidence

- Authoritative local done command: resolve from `AGENTS.md`.
- Targeted checks: run the narrow checks named by the active plan milestone.
- Integration and end-to-end proof: run every defined category in `AGENTS.md`;
  an undefined category remains an explicit verification gap.
- Evidence paths: record command output, artifacts, reviews, and remaining risks
  in the durable plan and `FINAL_HANDOFF.md`.

## Execution adapter

- Native Codex path: create an ExecPlan following `PLANS.md`, use scoped
  subagents only for disjoint work, and run the authoritative done command.
- Deterministic fallback: execute the ordered stories sequentially and record
  progress, decisions, and evidence in the same plan.
- OMX path: only after a compatible CLI probe, let OMX create and own its
  runtime state from this brief. This repository must not fabricate goals,
  ledgers, checkpoints, HUD state, or logs.

## Blocking unknowns

- None recorded. Add unresolved decisions here and to the decision ledger before
  implementation starts.
