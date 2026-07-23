# zero-to-hero skill evaluations

These evaluations exercise skill behavior separately from the hermetic release gate.
They follow OpenAI's skill-eval pattern:

1. define a small set of positive, contextual, and negative prompts;
2. run each prompt with `codex exec --json`;
3. retain the JSONL trace and isolated workspace;
4. apply deterministic checks before any model-based grading;
5. use a structured, read-only model grader only for qualitative handoff quality.

Authoritative guidance audited on 2026-07-22:

- <https://developers.openai.com/blog/eval-skills>
- <https://developers.openai.com/codex/skills/>
- <https://learn.chatgpt.com/docs/developer-commands?surface=cli>

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

The default run uses isolated temporary repositories, the least-permissive Codex sandbox
declared by each case, and bounded subprocess timeouts. It never fabricates a successful
trace when the Codex executable cannot actually run.
