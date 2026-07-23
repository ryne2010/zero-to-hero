# Final handoff

This repository is implementation-ready when the canonical docs, selected
profile contracts, neutral implementation brief, approved planning evidence,
and local validation harness all pass. OMX artifacts are optional CLI-owned
derivatives and are never a readiness prerequisite.

## Local Mode

Local Mode contains the full approved product surface using local services, synthetic data, and mocked or sandboxed external effects.

## Production Mode

Production Mode uses the same product surface with hosted/scaled infrastructure, production secrets, live providers, observability, SLOs, backups, and release gates.

## Required proof before implementation completion

- Source-of-truth map is valid.
- Decision ledger has no blocking unresolved decisions.
- `docs/implementation/PLANNING_EVIDENCE.md` records Planner, Architect, Critic,
  and explicit consensus evidence.
- The selected profile's required artifacts and negative assertions pass.
- Priority workflows have runtime evidence.
- The target-specific authoritative done command in `AGENTS.md` passes.
- Final review pass confirms no product-scope expansion or weakened invariants.

## External and physical effects

This handoff does not authorize production deployment, live-provider mutation,
credential use, fabrication, printing, flashing, energizing, or physical
actuation. Each requires a separate explicit downstream authorization and the
applicable human review gate.
