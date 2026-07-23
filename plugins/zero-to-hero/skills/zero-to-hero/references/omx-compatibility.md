# OMX compatibility contract

## Audited baseline

- audited date: `2026-07-22`;
- tested compatibility range: `==0.20.3`;
- tag: [`v0.20.3`](https://github.com/Yeachan-Heo/oh-my-codex/tree/v0.20.3);
- peeled tag commit: [`6c970cc12da256bfc7667edd0a9183b158d4a7a7`](https://github.com/Yeachan-Heo/oh-my-codex/commit/6c970cc12da256bfc7667edd0a9183b158d4a7a7);
- [package runtime requirement](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/package.json#L61-L62): Node.js `>=20`;
- [v0.20.3 release notes](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/docs/release-notes-0.20.3.md#L1-L5).

Only `0.20.3` has been tested. Do not infer compatibility from a later patch, minor, local skill cache, or catalog version.

Primary interface evidence:

- [Ultragoal CLI grammar](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/src/cli/ultragoal.ts#L36-L76);
- [runtime artifact creation and mutation](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/src/ultragoal/artifacts.ts#L805-L913);
- [Ultragoal lifecycle](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/skills/ultragoal/SKILL.md#L46-L180);
- [Ralplan consensus and handoff](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/skills/ralplan/SKILL.md#L44-L106);
- [Team ownership boundary](https://github.com/Yeachan-Heo/oh-my-codex/blob/6c970cc12da256bfc7667edd0a9183b158d4a7a7/skills/team/SKILL.md#L76-L80).

## Adapter behavior

`scripts/omx_adapter.py` performs a read-only compatibility probe:

1. resolve `omx` from the executable search path;
2. require `omx --version` to report exactly `oh-my-codex v0.20.3`;
3. inspect `omx ultragoal --help`;
4. require the audited commands, options, and artifact paths;
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
omx ultragoal checkpoint --goal-id <id> --status <complete|failed|blocked> ...
omx ultragoal record-review-blockers ...
```

`complete-goals` starts or resumes the current story. The aliases `complete`, `next`, and `start-next` map to it. There is no audited `start-story`, `complete-story`, `record-iteration`, `handoff`, or `recover` command.

The shell CLI cannot call interactive Codex goal tools. The leader reconciles the CLI handoff with `get_goal`, `create_goal`, and `update_goal`; synthetic tests provide snapshots through `--codex-goal-json`.

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
- prove Team-worker mutation is rejected without creating runtime artifacts.

The temporary repository is deleted after the test. Use `--require-omx` only when the compatible external integration is mandatory for the current gate.
