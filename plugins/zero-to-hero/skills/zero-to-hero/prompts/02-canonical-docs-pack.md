# Prompt: Canonical documentation pack

<!-- Generated from references/contract-graph.yaml::canonical_docs_pack. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Goal

- Create the canonical source-of-truth, decision, architecture, requirements, and handoff documentation required by the selected profiles.

## Context and required reads

- references/contract-graph.yaml
- Selected references/output-profiles/*.yaml files
- Approved capability and discovery evidence
- Existing authoritative target documentation

## Entry criteria

- Profile composition is approved and schema-valid
- Repository safety and instruction-trust checks have no blocking findings

## Constraints

- Generate only artifacts applicable to selected profiles
- Preserve existing files unless replacement is explicit and scoped
- Keep AGENTS.md concise, exact, and automatically discoverable

## Allowed writes

- .gitignore
- .gitattributes
- AGENTS.md
- PLANS.md
- CODEX.md
- FINAL_HANDOFF.md
- README.md
- docs/
- scripts/zero_to_hero_handoff_check.py
- docs/00-meta/generated-files.manifest.yaml
- Machine-enforced generated-harness exception to global path rules: scripts/zero_to_hero_handoff_check.py

## Forbidden writes

- Product runtime source
- User-level Codex configuration
- .omx runtime-owned files
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

- Target-specific AGENTS.md, self-contained PLANS.md contract, and concrete active ExecPlan
- Canonical source-of-truth and decision maps
- Profile-required substantive documentation
- Canonical generated-file provenance manifest
- Dependency-free generated handoff-readiness validator

## Evidence and checks

- Manifest validates against its schema
- Required and forbidden artifact assertions pass for selected profiles
- Existing-file preservation and post-write hashes are verified

## Stop or block when

- A profile-required template is missing or placeholder-only
- A write would replace an existing file without explicit scoped authorization
- Atomic staging or validation fails

## Done when

- Every selected profile's required artifact exists and is substantive
- The canonical manifest is finalized after all post-write checks

## Runtime implementation boundary

- Do not implement or modify product runtime code. Generate documentation, harness specifications, plans, and handoff artifacts only.
