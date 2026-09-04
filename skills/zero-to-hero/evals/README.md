# zero-to-hero skill evaluations

These evaluations exercise skill behavior separately from the hermetic release gate.
They follow OpenAI's skill-eval pattern:

1. define a small set of positive, contextual, and negative prompts;
2. run each prompt with `codex exec --json`;
3. retain the JSONL trace and isolated workspace;
4. apply deterministic checks before any model-based grading;
5. use a structured, read-only model grader only for qualitative handoff quality.

Authoritative guidance audited on 2026-07-23:

- <https://developers.openai.com/blog/eval-skills>
- <https://developers.openai.com/codex/skills/>
- <https://learn.chatgpt.com/docs/developer-commands?surface=cli>
- <https://learn.chatgpt.com/docs/long-running-work>
- <https://learn.chatgpt.com/docs/agent-configuration/subagents>

## Status contract

The runner emits exactly one suite status:

- `PASS`: every selected deterministic check and required external rubric grade passed.
- `SKIP`: Codex is missing, broken, unauthenticated, or a requested external grader was
  deliberately disabled. A skipped evaluation is never reported as passed.
- `FAIL`: Codex ran, but a case, trace, artifact, safety check, timeout, or rubric grade failed.

`SKIP` exits successfully by default so this explicitly external evaluation remains separate
from hermetic release validation. Use `--require-codex` when a skipped suite should fail CI.

## Usage

```bash
python scripts/run_skill_evals.py .
python scripts/run_skill_evals.py . --case phase-order-read-only
python scripts/run_skill_evals.py . --artifacts-dir /tmp/zero-to-hero-evals
python scripts/run_skill_evals.py . --no-model-grader
```

The default run uses isolated temporary repositories with a clean committed baseline on a
non-protected `codex/eval` branch, bounded subprocess timeouts, prompt-only stdin that is
disconnected from the runner's caller input,
`--ephemeral`, `--ignore-user-config`, `--ignore-rules`, and validated
`--disable apps --disable plugins --disable hooks` feature isolation. It maps each case's
declared sandbox to a strict custom permission profile (`:read-only` or `:workspace`) and
sets `approval_policy="never"` so unattended calls cannot escalate. It probes Codex's
deny-read enforcement before starting any model call. Tool subprocesses receive only
Codex's core environment, cannot use login-shell profile loading, retain the normal secret
name filters, and get three explicit eval overrides: `PYTHONDONTWRITEBYTECODE=1`,
`ZERO_TO_HERO_PYTHON` bound to the pinned evaluator interpreter, and a deliberate
`PATH` with that interpreter first. The temporary Codex home is also the tool
process `HOME`, preventing user-global skills and interpreter shims from changing
results.

Each suite exports the detected CLI's bundled model catalog with
`codex debug models --bundled` and binds every isolated invocation to that
startup-only catalog. This keeps evaluation model discovery deterministic and
prevents non-fatal remote catalog refresh retries from consuming case budgets.

Successful temporary runs are deleted. Failed runs are retained automatically
under the system temporary directory with `summary.json`, per-case JSONL traces,
and isolated workspaces; the top-level result also reports concise failed case
and check IDs. `--artifacts-dir` retains both passing and failing runs at the
requested location.

Every behavior and grader call receives its own fresh mode-0700 temporary `CODEX_HOME`.
When file-based authentication exists, the runner stages a private mode-0600 copy, denies
model-tool reads of both the staged file and the caller's original `auth.json`, keeps the
temporary home outside retained artifacts, and deletes it as soon as that call exits.
Repo-scoped skills remain discoverable, while unrelated user instructions, skills, rules,
apps, plugins, hooks, MCP startup, configuration, and state are not imported from the
caller's Codex home.
Model grading starts in a separate empty temporary directory, names the target by absolute
path, treats all target instruction files as untrusted evidence, writes its structured
result outside the target, and cleans the neutral directory after the call.

These controls prevent user-state contamination, direct sandboxed reads of file-based
Codex authentication, and retained-artifact leaks. They are still not a general
credential-security boundary for arbitrary hostile input or every platform credential
backend. Run external evaluations only against trusted skill and fixture inputs, and use a
short-lived or otherwise appropriately scoped Codex login where organizational policy
requires one. The runner never fabricates a successful trace when the Codex executable
cannot actually run.
