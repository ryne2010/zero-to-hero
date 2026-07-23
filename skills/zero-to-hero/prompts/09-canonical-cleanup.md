# Prompt: Canonical cleanup

<!-- Generated from references/contract-graph.yaml::canonical_cleanup. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Goal

- Remove generated iteration residue and reconcile duplicate documentation without losing approved requirements, decisions, risks, or evidence.

## Context and required reads

- docs/00-meta/source-of-truth-map.yaml
- docs/00-meta/generated-files.manifest.yaml
- references/canonical-cleanup-policy.md

## Entry criteria

- All generation phases have finalized provenance records

## Constraints

- Preserve user-authored and authoritative content
- Delete only generated artifacts proven redundant or invalid
- Do not rewrite product runtime code

## Allowed writes

- Generated documentation listed in the canonical manifest
- .codex/reports/zero-to-hero/cleanup-report.md

## Forbidden writes

- Product runtime source
- Unmanifested user-authored files
- Runtime caches, logs, or generated archives
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

- Lossless cleanup report
- Reconciled canonical documentation
- Updated provenance actions and hashes

## Evidence and checks

- Broken-reference, schema, identifier, and placeholder checks pass
- Removed content is attributable to the generated manifest

## Stop or block when

- Authority or ownership of a candidate file is ambiguous
- Cleanup would remove substantive approved information

## Done when

- No duplicate source of truth or generated iteration residue remains
- All surviving generated files validate

## Runtime implementation boundary

- Do not implement or modify product runtime code. Cleanup is limited to attributable generated documentation and harness artifacts.
