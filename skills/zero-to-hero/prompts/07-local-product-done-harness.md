# Prompt: Local product done harness

<!-- Generated from references/contract-graph.yaml::local_product_done_harness. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Goal

- Define one authoritative local done command and the exact build, test, lint, format, type, integration, and end-to-end evidence it composes.

## Context and required reads

- Target repository command inventory
- Selected profile evidence requirements
- references/local-product-done-harness.md
- PLANS.md

## Entry criteria

- Required commands have been resolved from repository evidence
- Priority behaviors and negative paths are documented

## Constraints

- Use exact commands that exist in the target repository
- Do not claim unavailable checks passed
- Keep external-model and external-tool evaluation separate from hermetic checks

## Allowed writes

- AGENTS.md
- PLANS.md
- docs/product-execution/
- .agents/skills/local-mode-verification/

## Forbidden writes

- Product runtime source
- User-level Codex configuration
- Fabrication, deployment, or live-effect scripts
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

- Exact command matrix and one authoritative local done command
- Runtime evidence, traceability, simulator, and negative-path contracts
- Scoped subagent ownership guidance

## Evidence and checks

- Every command is resolved from a file or an available project tool
- The local done command has defined success and failure interpretation
- Generated AGENTS.md names the actual layout and commands

## Stop or block when

- A required command cannot be resolved
- A claimed check cannot run in the documented environment

## Done when

- A new Codex session can verify the target using AGENTS.md and PLANS.md alone
- No unavailable integration is labeled passed

## Runtime implementation boundary

- Do not implement or modify product runtime code. Define the target-specific harness and verification contract only.
