# Codex / OMX handoff

OMX is an optional execution adapter. The durable handoff is a neutral implementation brief plus approved planning evidence; it must remain usable by native Codex when OMX is absent or incompatible.

See [OMX compatibility](omx-compatibility.md) for the audited version, probe contract, and executable integration test.

## Lifecycle

1. Run discovery or `$deep-interview` when material requirements remain unclear.
2. Ask the Ralplan Planner for the draft plan.
3. Complete Architect review before Critic review.
4. Complete Critic review against the Architect-reviewed draft.
5. Record an explicit consensus gate and its evidence.
6. Execute through native Codex Goal Mode or use `$ultragoal` when the adapter reports `PASS`.
7. Use Team only for independently owned parallel work in a supported environment.
8. Run independent code review and architecture-invariant review.
9. Run `$ultraqa` or the applicable final product verification.

`$ralph` is an explicitly selected single-owner alternate execution loop. It is not a mandatory review phase after Ultragoal.

## Neutral handoff

Always preserve these execution-neutral inputs outside `.omx/ultragoal/`:

- the traceable implementation brief;
- the Planner draft;
- Architect and Critic review evidence;
- the explicit consensus decision;
- validation commands, stop conditions, and unresolved blockers.

When OMX is missing or unsupported, use those inputs with native Codex planning and scoped subagents, or a deterministic sequential plan. Do not fabricate OMX-native files.

## Native Codex 0.145.0 path

Treat `PLANS.md` as the durable ExecPlan contract and maintain a separate active ExecPlan that follows it. When the outcome or execution scope is unclear, enter `/plan` and refine one observable outcome, constraints and non-goals, authority and external-effect boundaries, verification evidence, and the stop condition. Record the accepted result in that living ExecPlan, then enter `/goal`. Goal Mode provides thread-level continuity; it does not replace durable evidence or broaden authority.

Give each parallel Codex thread its own Git worktree and disjoint write ownership. Never give parallel threads write access to the same mutable working tree or shared generated/runtime state.

## Compatible OMX path

Probe without writing:

```bash
python <skill-root>/scripts/omx_adapter.py <target-repo> --json
```

After the probe reports `PASS`, explicitly authorize CLI-owned artifact creation:

```bash
python <skill-root>/scripts/omx_adapter.py <target-repo> \
  --require-compatible \
  --create-goals \
  --brief-file <neutral-implementation-brief> \
  --json
```

The adapter intentionally does not pass `--force` and refuses creation when any audited runtime artifact already exists.

Aggregate Ultragoal uses the Codex thread's active Goal Mode pointer. Do not run `/goal clear` before the first aggregate run or while a run is active. After an aggregate run reaches a terminal state, and only when another aggregate run will begin in the same Codex thread, run `/goal clear` before creating the second run.

## Ownership boundary

The compatible OMX CLI owns:

```text
.omx/ultragoal/brief.md
.omx/ultragoal/goals.json
.omx/ultragoal/ledger.jsonl
```

Do not template, hand-edit, locally schema-validate, or pre-create these files. Runtime and HUD state also remain OMX-owned.

The leader alone creates goals, steers the plan, records review blockers, and checkpoints Ultragoal state. Team workers return scoped evidence upward; they never mutate or checkpoint the leader's ledger.
