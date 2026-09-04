# OMX compatibility contract

## Audited baseline

- audited date: `2026-07-23`;
- tested compatibility range: `==0.20.3`;
- tag: [`v0.20.3`](https://github.com/Yeachan-Heo/oh-my-codex/tree/v0.20.3);
- peeled tag commit: [`6c970cc12da256bfc7667edd0a9183b158d4a7a7`](https://github.com/Yeachan-Heo/oh-my-codex/commit/6c970cc12da256bfc7667edd0a9183b158d4a7a7);
- [package runtime requirement](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/package.json#L61-L62): Node.js `>=20`;
- [v0.20.3 release notes](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/docs/release-notes-0.20.3.md#L1-L5).

Only `0.20.3` has been tested. Do not infer compatibility from a later patch, minor, local skill cache, or catalog version.

Primary interface evidence:

- [Ultragoal CLI grammar and structured steering parser](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/src/cli/ultragoal.ts);
- [runtime artifacts, steering invariants, mutations, and audit ledger](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/src/ultragoal/artifacts.ts);
- [Codex goal reconciliation and terminal cleanup notice](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/src/goal-workflows/codex-goal-snapshot.ts);
- [Ultragoal lifecycle](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/skills/ultragoal/SKILL.md#L46-L180);
- [Ralplan consensus and handoff](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/skills/ralplan/SKILL.md#L44-L106);
- [Team ownership boundary](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/skills/team/SKILL.md#L76-L80).

## Adapter behavior

`scripts/omx_adapter.py` performs a read-only compatibility probe:

1. resolve `omx` from the executable search path;
2. require `omx --version` to report exactly `oh-my-codex v0.20.3`;
3. inspect `omx ultragoal --help`;
4. require the audited commands, all six steering kinds, structured steering options,
   accepted/rejected/deduped audit wording, `/goal clear` boundary, and artifact paths;
5. create nothing unless `--create-goals --brief-file ...` is explicitly requested.

Use `omx ultragoal --help` for probing. Do not use `omx ultragoal create-goals --help`; v0.20.3 parses that as a creation attempt and reports a missing brief.

The creation path never passes `--force` and refuses to run when any audited runtime artifact already exists.

Result meanings are deliberate:

- `PASS`: exact audited version and interface were observed, or the explicitly requested CLI operation completed and its artifacts were verified;
- `SKIP`: an ordinary probe or integration test could not run because OMX was missing, unaudited, or interface-incompatible;
- `FAIL`: OMX was explicitly required but unsupported, a requested child process failed, or integration assertions failed.

An unavailable external test is therefore visible as `SKIP`, never as `PASS`.

## Supported v0.20.3 surface

The adapter depends on:

```text
omx ultragoal create-goals --brief-file <path> --json
omx ultragoal complete-goals --json
omx ultragoal status --json
omx ultragoal steer --kind <mutation-kind> --evidence <text> --rationale <text> ...
omx ultragoal steer --directive-json <json-or-path> --json
omx ultragoal checkpoint --goal-id <id> --status <complete|failed|blocked> ...
omx ultragoal record-review-blockers ...
```

`complete-goals` starts or resumes the current story. The aliases `complete`, `next`, and `start-next` map to it. There is no audited `start-story`, `complete-story`, `record-iteration`, `handoff`, or `recover` command.

The shell CLI cannot call interactive Codex goal tools. The leader reconciles the CLI handoff with `get_goal`, `create_goal`, and `update_goal`; synthetic tests provide snapshots through `--codex-goal-json`.

## Same-thread aggregate goal cleanup

New v0.20.3 plans default to one aggregate Codex goal for the durable plan. The
leader starts it with `create_goal`, keeps it active across intermediate OMX
stories, calls `update_goal({status: "complete"})` only after the final gate, gets
a fresh completed snapshot, and checkpoints that snapshot.

Before starting a second aggregate Ultragoal run in the same Codex
thread/session, run `/goal clear` in the Codex UI. That removes the completed
thread goal before the next `create_goal`. OMX prints this terminal next step but
does not invoke `/goal clear`, `thread/goal/clear`, or another hidden reset route.
If a future documented Codex tool exposes clear/reset, prefer that tool.

The adapter proves this boundary twice: its read-only help probe requires the
same-thread `/goal clear` contract, and the external integration completes a
synthetic aggregate run and requires the terminal cleanup notice.

## Structured steering

Steering is explicit, structured, and evidence-backed:

```text
omx ultragoal steer \
  --kind <add_subgoal|split_subgoal|reorder_pending|revise_pending_wording|annotate_ledger|mark_blocked_superseded> \
  --evidence <text> \
  --rationale <text> \
  [--target-goal-id <id>] \
  [--title <text>] \
  [--objective <text>] \
  [--after-json <json-or-path>] \
  [--idempotency-key <key>] \
  [--json]

omx ultragoal steer --directive-json <json-or-path> [--json]
```

Every proposal requires non-empty `evidence` and `rationale`. The accepted
sources are `cli`, `finding`, and `user_prompt_submit`; the default is `cli`.
The v0.20.3 parser also accepts `--source`, although the published help does not
list it, so do not treat that flag as portable beyond the exact audited version.

Mutation semantics:

| Kind | Required structured input | Audited effect |
| --- | --- | --- |
| `add_subgoal` | top-level `title` and `objective` | Append one pending, schedule-eligible goal. |
| `split_subgoal` | pending `targetGoalId`; `after.children[]` with non-empty `title` and `objective` | Retain the parent as `superseded`, append replacement children, and link both directions. |
| `reorder_pending` | `after.pendingGoalIds[]` (or directive `pendingOrder[]`) | Move the unique, schedule-eligible pending ids to the requested front order. |
| `revise_pending_wording` | pending `targetGoalId`; at least one of `title` or `objective`, either top-level or under `after` | Change wording while preserving status and completion evidence. |
| `annotate_ledger` | evidence and rationale; target optional | Append an audit annotation without writing a changed plan. |
| `mark_blocked_superseded` | existing `targetGoalId`; optional `after.children[]` | Without children, mark the retained goal `blocked`; with children, retain it as `superseded` and append replacements. |

`--after-json` and `--directive-json` accept either inline JSON or a JSON file
path. An accepted `--idempotency-key` replay returns `deduped: true` and reuses
the original accepted audit; it does not append a duplicate ledger entry.

Target nuance in v0.20.3 is intentionally pinned. The first help synopsis
advertises `--target-goal-ids`, but the executable parser only consumes
`--target-goal-id`; passing the plural flag is rejected as positional prose.
Directive `targetGoalIds` is normalized to its first non-empty id. Use
`after.pendingGoalIds` or directive `pendingOrder` for `reorder_pending`. The
adapter records this advertised-only defect but does not require or execute the
plural flag; generated workflows must not depend on it.

### Audit and invariants

Accepted proposals append `steering_accepted`; invariant-rejected structured
proposals append `steering_rejected` and return nonzero. A deduped replay returns
the prior accepted audit with `deduped: true`. Parse-level failures such as broad
natural-language steering or the unusable plural target flag fail before a
proposal exists, so they do not mutate the plan or ledger.

Steering must not:

- edit the aggregate Codex objective, original brief/constraints, quality gates,
  completion fields, or an already completed aggregate plan;
- weaken or bypass tests, verification, review, or completion;
- hard-delete goals or auto-complete work;
- split or revise a non-pending goal;
- silently guess a mutation from broad prose.

Superseded goals remain audit-visible but are skipped by scheduling. A blocked
goal without replacements is also skipped by scheduling but continues to block
final completion until later explicit steering replaces or supersedes it.

## Runtime ownership

Only the compatible CLI creates and mutates:

```text
.omx/ultragoal/brief.md
.omx/ultragoal/goals.json
.omx/ultragoal/ledger.jsonl
```

Do not ship templates or a local duplicate schema for these files. `.omx/state/.../ultragoal-state.json`, HUD state, locks, and logs are runtime-owned as well.

Ultragoal is leader-owned. Processes marked `OMX_TEAM_WORKER` or `OMX_TEAM_INTERNAL_WORKER` must be rejected from mutations. Team is an explicit, conditional parallel-execution choice; workers submit evidence to the leader and do not edit or checkpoint the ledger.

## Lifecycle and final gate

The supported sequence is discovery/deep interview when needed, Ralplan Planner draft, Architect review, Critic review, explicit consensus, Ultragoal, conditional Team work, independent code-reviewer and Architect invariant review, then `$ultraqa` or the applicable product verification.

Final Ultragoal completion requires a completed Codex goal snapshot and a quality-gate payload with:

- anti-slop cleanup evidence;
- passing verification commands;
- independent code-reviewer `APPROVE` evidence;
- Architect `CLEAR` evidence;
- a passing architecture-invariant gate.

Use `record-review-blockers` when final review is not clean. `$ralph` remains an explicit single-owner alternate to Ultragoal, never a mandatory post-Ultragoal pass.

## Neutral fallback

If probing reports `SKIP`, retain the implementation brief and approved Ralplan evidence outside `.omx/ultragoal/`. Continue through native Codex planning with scoped subagents or a deterministic sequential plan. Missing or unsupported OMX never justifies fabricated goals, ledger, state, or successful integration evidence.

## Executable verification

Run:

```bash
python scripts/test_omx_integration.py --json
```

When v0.20.3 is compatible, the test uses a temporary repository to:

- let the CLI create two goals;
- read initial status;
- start and complete the first synthetic story;
- start the second story and record a non-terminal blocker;
- verify the exact ledger event sequence;
- prove Team-worker mutation is rejected without creating runtime artifacts;
- exercise all six structured steering kinds through real CLI mutations;
- cover singular targets, `--after-json`, a file-backed `--directive-json`,
  sources, and idempotent replay;
- prove accepted and rejected ledger audits, dedupe reuse, protected-state
  invariants, no hard deletion, and no auto-completion;
- prove broad prose and the advertised-only plural target flag fail without
  mutation;
- finish a synthetic aggregate goal and require the same-thread `/goal clear`
  terminal notice while proving OMX does not call a hidden clear route.

The temporary repository is deleted after the test. Use `--require-omx` only when the compatible external integration is mandatory for the current gate.
