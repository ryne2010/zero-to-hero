# Prompt: Design and visual contract pack

<!-- Generated from references/contract-graph.yaml::design_and_visual_pack. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Applicability

- profiles_any: web-app, mobile-app, desktop-app

## Goal

- Convert approved visual direction into explicit screen, interaction, asset, and validation contracts without implementing the interface.

## Context and required reads

- Approved design direction or visual references
- Selected UI-capable profile YAML
- docs/00-meta/source-of-truth-map.yaml

## Entry criteria

- A UI-capable profile is selected
- Visual direction is approved or explicitly marked unresolved

## Constraints

- Treat generated or imported imagery as evidence until approved
- Record inferred behavior as a decision, not as fact
- Include accessibility and negative states

## Allowed writes

- docs/ui/
- docs/design/
- .codex/reports/zero-to-hero/visual-approval-ledger.md

## Forbidden writes

- Product runtime source
- UI component implementation
- Unapproved canonical visual assets
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

- Approved direction contract
- Screen, route, interaction, and asset contracts
- Visual validation evidence policy

## Evidence and checks

- Every priority workflow has normal, empty, loading, error, and permission states
- Visual provenance and approval status are recorded

## Stop or block when

- Required visual direction is unapproved
- A visual implies unresolved product behavior

## Done when

- Another agent can implement the UI without hidden visual assumptions
- Visual acceptance is observable and testable

## Runtime implementation boundary

- Do not implement or modify product runtime code or UI components. Produce approved visual and interaction contracts only.
