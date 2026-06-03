# Canonical handoff

This repository is a docs-first implementation harness. It is ready for Codex/OMX implementation when all source-of-truth docs, design contracts, product-execution harnesses, and local-product verification gates are present and validated.

## Hard invariants

- Do not enable real-world effects in local mode.
- Do not use real PII in tests, fixtures, screenshots, docs, or generated visuals.
- Do not implement unsupported product claims.
- Keep source-of-truth docs canonical and free of iteration noise.
- Preserve unresolved decisions explicitly.
