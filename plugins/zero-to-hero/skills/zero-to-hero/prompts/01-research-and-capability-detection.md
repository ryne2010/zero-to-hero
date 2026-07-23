# Prompt: Research and capability detection

<!-- Generated from references/contract-graph.yaml::research_and_capability_detection. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Goal

- Reconcile exact repository evidence with approved discovery data and audit time-sensitive external facts from primary sources.

## Context and required reads

- .codex/reports/zero-to-hero/approved-capabilities.json or equivalent approved evidence
- Target repository marker files
- references/source-research-policy.md
- references/source-links.md

## Entry criteria

- Approved discovery evidence exists or the repository has sufficient unambiguous markers

## Constraints

- Use exact positive and negative capability markers
- Do not treat generic CMake as firmware proof
- Record source URL, version or commit, and audited date for current external claims

## Allowed writes

- .codex/reports/zero-to-hero/capability-report.yaml
- .codex/reports/zero-to-hero/source-notes.md
- .codex/reports/zero-to-hero/research-queue.md

## Forbidden writes

- Product runtime source
- Generated hardware or fabrication outputs
- .omx runtime state
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

- Exact detected capabilities with evidence and negative evidence
- Selected composable output profiles with provenance
- Audited external source notes

## Evidence and checks

- Capability detector output is machine-readable
- Selected profiles are derivable from profile YAML
- Unsupported or ambiguous markers remain unresolved rather than guessed

## Stop or block when

- A required current fact cannot be verified
- Approved capability data conflicts with repository evidence in a safety-relevant way

## Done when

- Every selected profile has approved or repository evidence
- Negative markers prevent known false-positive project families

## Runtime implementation boundary

- Do not implement or modify product runtime code. Research and capability reports are the only outputs.
