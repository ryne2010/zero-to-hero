# Prompt: One-shot small product preparation

<!-- Generated from references/contract-graph.yaml::one_shot_small_product. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Goal

- Prepare a narrowly scoped, low-risk repository in one bounded generation run while preserving every normal contract and safety gate.

## Context and required reads

- references/contract-graph.yaml
- Approved capability data
- Selected profile YAML files

## Entry criteria

- Scope is small, explicit, low-risk, and has no blocking ambiguity

## Constraints

- Do not skip schema, safety, trust, provenance, or required-artifact checks
- Use the same atomic generator and canonical manifest as the full workflow

## Allowed writes

- Only graph and profile-authorized generated artifacts

## Forbidden writes

- Product runtime source
- Unscoped replacement of existing files
- .omx runtime state unless explicitly requested through a compatible CLI
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

- Profile-complete generated harness and documentation
- Canonical provenance manifest
- Neutral implementation handoff

## Evidence and checks

- All normal release and target audit checks pass
- No placeholder-only artifact satisfies a required exit

## Stop or block when

- Scope expands beyond a small bounded preparation task
- Any normal phase stop condition is reached

## Done when

- The same readiness criteria as the canonical workflow pass
- The run remains documentation and harness generation only

## Runtime implementation boundary

- Do not implement or modify product runtime code. One-shot mode only compresses orchestration, never the safety or evidence contract.
