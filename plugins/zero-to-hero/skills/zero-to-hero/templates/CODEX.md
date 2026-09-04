# Codex handoff

`AGENTS.md` contains the automatically discovered operating contract. This file
adds execution-adapter detail; it does not override `AGENTS.md`.

Start from the neutral brief in
`docs/implementation/IMPLEMENTATION_BRIEF.md` and the durable planning contract
in `PLANS.md`. The living plan is `docs/implementation/EXECPLAN.md`.

## Planning and execution lifecycle

1. Complete discovery or a deep interview when requirements are incomplete.
2. Produce a Planner draft.
3. Run an Architect review.
4. Run a Critic review after the Architect.
5. Record explicit consensus in
   `docs/implementation/PLANNING_EVIDENCE.md`.
6. Execute through native Codex, deterministic sequential work, or compatible
   OMX Ultragoal.
7. Use Team/parallel agents only when supported and write ownership is disjoint.
8. Run independent code and architecture-invariant reviews.
9. Run UltraQA or the applicable final product verification.

Ralph is an explicitly selected alternate single-owner loop, not a mandatory
post-Ultragoal review phase.

## Native Codex 0.145.0 path

Keep `docs/implementation/EXECPLAN.md` current under the durable contract in
`PLANS.md`. When the outcome or scope is unclear, use `/plan` to refine one
observable outcome, its constraints and non-goals, and the verification
evidence and stop condition. Record the accepted result in that living
ExecPlan, then use `/goal` for thread-level continuity. Goal Mode does not
replace repository evidence or broaden authority.

Give each parallel Codex thread its own Git worktree and disjoint write
ownership. Parallel threads must not share write access to one mutable working
tree or shared generated/runtime state.

## OMX boundary

Probe the installed CLI before use. A compatible OMX CLI creates and owns its
runtime state from the neutral brief. Do not hand-author goals, ledgers,
checkpoints, HUD state, or logs. Only the leader mutates Ultragoal state; workers
return evidence.

For aggregate Ultragoal runs in one Codex thread, do not clear the first or an
active run. After a run reaches a terminal state, and only before starting a
second aggregate run in that same thread, run `/goal clear`.

If OMX is missing or incompatible, retain the same brief and evidence contract
and use native Codex planning/subagents or deterministic sequential execution.

Keep sandboxing strict. Real providers, credentials, production data,
deployment, and physical effects remain disabled until separately authorized.
