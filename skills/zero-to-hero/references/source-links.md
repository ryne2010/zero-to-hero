# Audited primary sources

Audited on **2026-07-23**. Recheck current primary sources before changing an
interface, compatibility claim, safety boundary, or time-sensitive practice.

## Codex

- [Codex documentation](https://learn.chatgpt.com/docs) — agent workflows,
  repository instructions, tools, and task execution.
- [Codex best practices](https://learn.chatgpt.com/guides/best-practices) —
  repository context, verification, clear task boundaries, and review.
- [Long-running work](https://learn.chatgpt.com/docs/long-running-work) —
  native `/plan` to `/goal` handoff, durable outcomes and verification, and
  isolated worktrees for parallel work.
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
  — current native-subagent behavior, inspection, delegation, and parallel-write
  cautions.
- [Codex ExecPlans](https://developers.openai.com/cookbook/articles/codex_exec_plans)
  — self-contained living plans with progress, discoveries, decisions,
  milestones, validation, and recovery.
- [Evaluating skills](https://developers.openai.com/blog/eval-skills) —
  explicit, implicit/contextual, and negative cases; JSONL traces; deterministic
  checks; schema-constrained rubric grading; and separate external grading.
- [Agent Skills](https://developers.openai.com/codex/skills) — skill packaging
  and discovery.
- [Build skills](https://learn.chatgpt.com/docs/build-skills) — current
  `SKILL.md`, progressive-disclosure, and optional UI metadata guidance.
- [Build plugins](https://learn.chatgpt.com/docs/build-plugins) — current
  plugin manifest, relative-path, and marketplace contracts.
- [AGENTS.md guidance](https://developers.openai.com/codex/guides/agents-md) —
  automatically discovered repository instructions.
- [Sandboxing and security](https://developers.openai.com/codex/concepts/sandboxing)
  — approval and filesystem/network boundaries.

The local compatibility probe resolves `codex-cli 0.145.0` to its optional
Darwin ARM64 package, verifies the native executable, `codex exec` automation
flags, ChatGPT authentication, and a successful WebSocket handshake. The
external behavior and handoff-grader suites remain authoritative for the final
`PASS`, `SKIP`, or `FAIL` result; binary availability alone is not reported as
a passed model-backed evaluation.

## OMX

- [oh-my-codex v0.20.3](https://github.com/Yeachan-Heo/oh-my-codex/tree/v0.20.3)
  — audited tag.
- Tag commit:
  [`6c970cc12da256bfc7667edd0a9183b158d4a7a7`](https://github.com/Yeachan-Heo/oh-my-codex/commit/6c970cc12da256bfc7667edd0a9183b158d4a7a7).

The local interface probe found OMX v0.20.3 on Node 20. Supported Ultragoal
operations and the tested range are documented in `omx-compatibility.md`.
Runtime schemas remain CLI-owned.

## Mechanical CAD and robotics geometry

- [`earthtojake/text-to-cad` v0.3.9](https://github.com/earthtojake/text-to-cad/tree/0.3.9)
  — audited tag.
- Tag commit:
  [`fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423`](https://github.com/earthtojake/text-to-cad/commit/fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423).
- Release source commit:
  [`ac2659a1e7256b030a87dd4d45a37dcdccce6b45`](https://github.com/earthtojake/text-to-cad/commit/ac2659a1e7256b030a87dd4d45a37dcdccce6b45).
- [`step.parts`](https://github.com/earthtojake/step.parts) and its
  [third-party notices](https://github.com/earthtojake/step.parts/blob/main/THIRD_PARTY_NOTICES.md)
  — upstream project licensing and third-party provenance boundaries.

`text-to-cad` is MIT licensed. Third-party part models retain their source
licenses, and the part API is not sufficient proof of a per-model license.
Unknown licensing remains visible and blocks redistribution or fabrication when
license evidence is required. The audited v0.3.9 `cad-viewer` instructions
reference a missing `agent:start` package script; use deterministic inspection
and snapshot fallback unless a live probe proves the viewer operational.

## Validator dependencies

- [PyYAML 6.0.3](https://pypi.org/project/PyYAML/6.0.3/)
- [jsonschema 4.26.0](https://pypi.org/project/jsonschema/4.26.0/)

The release environment pins these versions so schema parsing is mandatory
rather than silently skipped.

## Instruction trust

- [OWASP Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
  — untrusted-content separation, least privilege, validation, and monitoring.
