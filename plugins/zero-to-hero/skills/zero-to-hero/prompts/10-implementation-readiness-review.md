# Prompt: Implementation readiness review

<!-- Generated from references/contract-graph.yaml::implementation_readiness_review. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Goal

- Independently verify that the repository is safe, concrete, profile-complete, and executable by a new Codex session.

## Context and required reads

- AGENTS.md
- PLANS.md
- FINAL_HANDOFF.md
- docs/00-meta/generated-files.manifest.yaml
- Selected profile YAML files

## Entry criteria

- Canonical cleanup is complete
- All required artifacts and planning evidence exist

## Constraints

- Review evidence rather than summaries
- Do not label skipped or unavailable checks passed
- Keep implementation and physical authorization downstream

## Allowed writes

- .codex/reports/zero-to-hero/final-readiness.md
- FINAL_HANDOFF.md

## Forbidden writes

- Product runtime source
- Fabrication, deployment, energizing, or actuation actions
- .omx leader state from a Team worker
- Machine-enforced global path rule: .codex/config.toml
- Machine-enforced global path rule: .omx/**
- Machine-enforced global path rule: **/*.c
- Machine-enforced global path rule: **/*.cc
- Machine-enforced global path rule: **/*.cpp
- Machine-enforced global path rule: **/*.cs
- Machine-enforced global path rule: **/*.dart
- Machine-enforced global path rule: **/*.go
- Machine-enforced global path rule: **/*.gcode
- Machine-enforced global path rule: **/*.java
- Machine-enforced global path rule: **/*.js
- Machine-enforced global path rule: **/*.jsx
- Machine-enforced global path rule: **/*.kt
- Machine-enforced global path rule: **/*.kts
- Machine-enforced global path rule: **/*.py
- Machine-enforced global path rule: **/*.rs
- Machine-enforced global path rule: **/*.step
- Machine-enforced global path rule: **/*.stl
- Machine-enforced global path rule: **/*.stp
- Machine-enforced global path rule: **/*.swift
- Machine-enforced global path rule: **/*.ts
- Machine-enforced global path rule: **/*.tsx
- Machine-enforced global path rule: **/*.3mf

## Expected outputs

- Profile-aware readiness verdict
- Exact verification results and skipped external integrations
- Remaining unknowns and explicit blockers

## Evidence and checks

- Required, forbidden, prompt-contract, schema, provenance, and safety checks pass
- AGENTS.md and PLANS.md are target-specific and self-contained
- Independent review and architecture-invariant review are specified

## Stop or block when

- Any required artifact is missing or placeholder-only
- Any unsafe state, child failure, schema error, or unsupported requested tool remains

## Done when

- A fresh agent can implement and verify the target without hidden context
- No known blocking error remains

## Runtime implementation boundary

- Do not implement or modify product runtime code. This phase reviews and reports readiness only.
