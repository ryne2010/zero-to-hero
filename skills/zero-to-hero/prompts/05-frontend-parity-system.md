# Prompt: Frontend parity contract

<!-- Generated from references/contract-graph.yaml::frontend_parity_pack. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Applicability

- profiles_any: web-app, mobile-app, desktop-app

## Goal

- Define deterministic parity evidence that links approved visual targets to routes, components, data states, and user workflows.

## Context and required reads

- Approved visual contracts
- Selected UI profile YAML
- references/frontend-parity-system.md

## Entry criteria

- Design and visual contracts are approved
- Priority routes and workflows are known

## Constraints

- No scaffold-only screens or dead controls
- Evidence must cover responsive, accessibility, and negative states

## Allowed writes

- docs/ui/frontend-parity-system/
- docs/ui/FRONTEND_CONTEXT.md
- .agents/skills/frontend-parity/

## Forbidden writes

- Product runtime source
- Frontend component implementation
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

- Route and component parity contracts
- Golden flow and screenshot evidence policy
- No-scaffold and no-dead-control rules

## Evidence and checks

- Every priority control maps to behavior or an explicit disabled reason
- Parity checks identify exact commands and expected evidence paths

## Stop or block when

- Priority visual targets are not approved
- Required behavior remains implicit

## Done when

- Parity can be graded from deterministic evidence
- The contract contains no placeholder-only exits

## Runtime implementation boundary

- Do not implement or modify frontend runtime code. Produce parity contracts and evidence requirements only.
