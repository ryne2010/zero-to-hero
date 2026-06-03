# Final handoff

This repository is implementation-ready when the canonical docs, product contracts, harness checks, and OMX artifacts all pass validation.

## Local Mode

Local Mode contains the full approved product surface using local services, synthetic data, and mocked or sandboxed external effects.

## Production Mode

Production Mode uses the same product surface with hosted/scaled infrastructure, production secrets, live providers, observability, SLOs, backups, and release gates.

## Required proof before implementation completion

- Source-of-truth map is valid.
- Decision ledger has no blocking unresolved decisions.
- Priority workflows have runtime evidence.
- Local product done gate passes.
- Final review pass confirms no product-scope expansion or weakened invariants.
