# Prompt: Product usability contract

<!-- Generated from references/contract-graph.yaml::product_usability_pack. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Goal

- Specify complete, observable product workflows including validation, persistence, permissions, failure handling, and state transitions.

## Context and required reads

- Canonical product workflows
- Selected profile evidence requirements
- references/product-usability-contract.md

## Entry criteria

- Priority workflows and non-goals are approved

## Constraints

- Every priority action must have an observable result
- Every form or command must define validation and failure behavior
- Local and production effects must remain distinct

## Allowed writes

- docs/product-execution/
- .agents/skills/product-usability/

## Forbidden writes

- Product runtime source
- Live provider configuration
- Production data
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

- Action-binding and workflow transaction contracts
- Scenario, role, permission, error, and recovery contracts
- No-dead-ends policy

## Evidence and checks

- Priority workflows have success and negative-path acceptance evidence
- External effects are disabled or simulated in local verification

## Stop or block when

- A priority workflow lacks an approved outcome
- A local test would cause an external effect

## Done when

- Every priority workflow is implementable and independently verifiable
- Failure and recovery states are explicit

## Runtime implementation boundary

- Do not implement or modify product runtime code. Produce usability, workflow, and verification contracts only.
