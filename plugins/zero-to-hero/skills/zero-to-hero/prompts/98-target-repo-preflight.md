# 98 — target repo preflight audit

Use this optional prompt before the deep interview when the user provides an existing repo and wants to understand what already exists.

```txt
Use the zero-to-hero skill.

Perform a target repository preflight audit only. Do not implement product code and do not generate the full docs pack yet.

Read:
- AGENTS.md, CODEX.md, FINAL_HANDOFF.md if present
- README.md
- package/build/test configuration
- docs/ if present
- .omx/ if present
- .agents/skills/ if present
- current app source tree only enough to inventory capabilities

Run or emulate:
- capability detection
- source-of-truth inventory
- harness layer inventory
- instruction-trust risk scan
- target repo pre-mortem

Produce:
- .codex/reports/zero-to-hero/target-repo-preflight.md
- .codex/reports/zero-to-hero/capability-report.json
- .codex/reports/zero-to-hero/recommended-zero-to-hero-path.md

Return:
1. detected capabilities and confidence;
2. existing source-of-truth artifacts;
3. missing harness layers;
4. likely failure modes if implementation continues now;
5. recommended next zero-to-hero phase;
6. files that should not be touched.
```
