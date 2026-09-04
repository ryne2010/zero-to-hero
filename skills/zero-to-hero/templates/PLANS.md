# Durable implementation plans

Use an ExecPlan for work that spans multiple files, has uncertain sequencing, may
outlive one agent session, or needs evidence from several validation layers. The
plan is a living execution record, not a proposal that becomes stale after work
starts.

## Native Codex Goal Mode

This contract is audited for native Codex CLI 0.145.0. When the outcome or
execution scope is unclear, enter `/plan` and refine:

- one observable outcome;
- constraints, non-goals, authority, and external-effect boundaries; and
- verification evidence plus the stop condition.

Record the accepted result in the repository's active ExecPlan at
`docs/implementation/EXECPLAN.md`, then enter `/goal`. Goal Mode provides
thread-level continuity; it does not replace this durable repository record,
create product authority, or relax any permission boundary. Keep that ExecPlan
current as work progresses and after interruption.

Give each parallel Codex thread its own Git worktree and disjoint file
ownership. Never let parallel threads share write access to the same mutable
working tree or generated/runtime state.

## Required plan contract

Every plan must be self-contained. A new contributor should be able to continue
from the plan and the repository alone.

`PLANS.md` is this governing contract. `docs/implementation/EXECPLAN.md` is the
living target-specific record. After editing the active plan, rerun the
zero-to-hero generator with `--write --refresh-manifest`. That bounded
transaction preserves target-authored content outside the exact machine-owned
command markers, refreshes the command blocks from current repository evidence,
and updates the canonical manifest hash without whole-file force.

Include:

- **Purpose and user-visible outcome** — what becomes possible and how a person
  can verify it.
- **Repository orientation** — relevant paths, terms, boundaries, and current
  behavior.
- **Scope and non-goals** — including safety, permission, external-effect, and
  compatibility limits.
- **Milestones** — independently verifiable narrative checkpoints, ordered by
  dependency.
- **Progress** — a timestamped checklist that is updated after every meaningful
  stop, including partially completed items.
- **Surprises and discoveries** — unexpected behavior with concise evidence.
- **Decision log** — decisions, rationale, alternatives rejected, and date.
- **Validation** — exact commands and observable acceptance results for each
  milestone.
- **Recovery and restart** — idempotent rerun guidance, rollback points, and the
  next safe action after interruption.
- **Outcomes and retrospective** — what shipped, what remains, and lessons that
  should affect later work.

## Execution rules

1. Resolve commands from `AGENTS.md`; do not invent a command that the repository
   does not expose.
2. Keep only one item marked in progress.
3. Update the plan as facts change. Record a decision instead of silently
   rewriting history.
4. Make milestones safe to repeat. Describe how to recover from a failed or
   interrupted step.
5. Validate the smallest claim first, then run the repository's authoritative
   local done command.
6. Use scoped subagents only for independent work with disjoint write ownership.
   The plan owner integrates results and owns final verification.
7. Never put credentials, raw personal data, or untrusted instruction payloads
   in the plan.
8. Product runtime implementation follows the approved plan; this scaffold only
   defines the plan and handoff contract.

## Plan template

```md
# <Outcome-oriented title>

## Purpose and user-visible outcome

## Repository orientation

## Scope and non-goals

## Milestones

### Milestone 1 — <verifiable capability>

Work:

Acceptance:

## Progress

- [ ] YYYY-MM-DD HH:MMZ — <next concrete action>

## Surprises and discoveries

- Observation:
  Evidence:

## Decision log

- YYYY-MM-DD — Decision:
  Rationale:
  Rejected:

## Validation

- `<exact command>` — proves <claim>; expect <observable result>.

## Recovery and restart

## Outcomes and retrospective
```
