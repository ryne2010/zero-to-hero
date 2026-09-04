# Final handoff

This repository's handoff is implementation-ready when the canonical docs,
selected profile contracts, neutral implementation brief, current
`docs/implementation/EXECPLAN.md`, approved planning evidence, and generated
handoff validator all pass. OMX artifacts are optional CLI-owned derivatives
and are never a readiness prerequisite.

The generated `scripts/zero_to_hero_handoff_check.py` proves handoff-baseline
integrity only. Its embedded artifact selection must match the manifest, and
the machine-owned command blocks in `AGENTS.md` and the active ExecPlan must
match. After target-owned documentation changes, run the manifest's explicit
`--write --refresh-manifest` command before this check. Before claiming product
implementation complete, compose it with the repository's real build, test,
lint, type, integration, end-to-end, and runtime-evidence checks through the
authoritative command in `AGENTS.md`.

## Local Mode

Local Mode contains the full approved product surface using local services, synthetic data, and mocked or sandboxed external effects.

## Production Mode

Production Mode uses the same product surface with hosted/scaled infrastructure, production secrets, live providers, observability, SLOs, backups, and release gates.

## Required proof before implementation completion

- Source-of-truth map is valid.
- Decision ledger has no blocking unresolved decisions.
- `docs/implementation/PLANNING_EVIDENCE.md` records Planner, Architect, Critic,
  and explicit consensus evidence.
- `docs/implementation/EXECPLAN.md` is current, target-specific, and records
  progress, decisions, validation, recovery, and outcomes.
- The selected profile's required artifacts and negative assertions pass.
- Priority workflows have runtime evidence.
- The target-specific authoritative done command in `AGENTS.md` passes.
- Final review pass confirms no product-scope expansion or weakened invariants.

## External and physical effects

This handoff does not authorize production deployment, live-provider mutation,
credential use, fabrication, printing, flashing, energizing, or physical
actuation. Each requires a separate explicit downstream authorization and the
applicable human review gate.
