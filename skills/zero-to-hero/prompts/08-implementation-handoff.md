# Prompt: Neutral implementation handoff and optional OMX adapter

<!-- Generated from references/contract-graph.yaml::implementation_handoff. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Goal

- Create a neutral, traceable implementation brief and approved planning evidence that native Codex can execute with or without OMX.

## Context and required reads

- docs/implementation/IMPLEMENTATION_BRIEF.md
- docs/implementation/PLANNING_EVIDENCE.md
- PLANS.md
- references/codex-omx-handoff.md
- references/omx-compatibility.md

## Entry criteria

- Canonical documentation and harness contracts are complete
- Planner, Architect, and Critic evidence can be recorded in order

## Constraints

- Use Planner then Architect then Critic, followed by an explicit consensus gate
- Treat OMX as optional and interface-probed
- Leader alone owns Ultragoal state; Team workers return evidence only
- Ralph is an explicitly selected alternate execution loop

## Allowed writes

- docs/implementation/IMPLEMENTATION_BRIEF.md
- docs/implementation/PLANNING_EVIDENCE.md
- FINAL_HANDOFF.md
- .omx/ultragoal/ only through a compatible OMX CLI explicitly requested by the user

## Forbidden writes

- Hand-authored .omx goals.json or ledger.jsonl
- .omx runtime state, HUD state, logs, or worker checkpoints
- Product runtime source
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

- Neutral implementation brief with ordered stories and dependencies
- Planner, Architect, Critic, and consensus evidence
- Native ExecPlan or deterministic sequential fallback
- Optional OMX CLI command only when compatibility probing passes

## Evidence and checks

- OMX probe records version and required interface tokens when requested
- Unsupported or missing OMX yields a neutral fallback
- The brief is executable without conversation history

## Stop or block when

- Consensus is not explicit
- OMX is requested but its version or interface is unsupported
- A worker attempts to mutate leader-owned state

## Done when

- The handoff is implementation-ready under native Codex
- Any OMX state was created only by the supported CLI

## Runtime implementation boundary

- Do not implement or modify product runtime code. Produce the neutral brief, planning evidence, and optional CLI-created handoff only.
