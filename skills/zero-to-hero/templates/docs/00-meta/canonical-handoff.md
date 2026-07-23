# Canonical handoff

This repository is a docs-first implementation harness. It is ready for later
implementation when the selected profile contracts, neutral brief, approved
planning evidence, and target-specific validation gate are present and pass.
Native Codex is the default execution surface; a compatible OMX CLI is an
optional adapter.

## Hard invariants

- Do not enable real-world effects in local mode.
- Do not use real PII in tests, fixtures, screenshots, docs, or generated visuals.
- Do not implement unsupported product claims.
- Keep source-of-truth docs canonical and free of iteration noise.
- Preserve unresolved decisions explicitly.
- Never fabricate optional runtime state or count a skipped integration as
  passed.
- Require a separate explicit authorization for production, fabrication,
  deployment, flashing, energizing, or physical actuation.

## Readiness evidence

- `AGENTS.md` records actual layout, exact repository commands, and one local
  done command.
- `PLANS.md` defines restartable long-running execution.
- `docs/implementation/IMPLEMENTATION_BRIEF.md` is execution-neutral.
- `docs/implementation/PLANNING_EVIDENCE.md` records ordered review and
  consensus.
- `docs/00-meta/generated-files.manifest.yaml` proves the scaffold transaction.
- Profile-specific contracts supply applicable acceptance and negative evidence.
