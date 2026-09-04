# Prompt: Neutral implementation handoff and optional OMX adapter

<!-- Generated from references/contract-graph.yaml::implementation_handoff. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Goal

- Create a neutral, traceable implementation brief and approved planning evidence that native Codex can execute with or without OMX.

## Context and required reads

- docs/implementation/IMPLEMENTATION_BRIEF.md
- docs/implementation/EXECPLAN.md
- docs/implementation/PLANNING_EVIDENCE.md
- PLANS.md
- references/codex-omx-handoff.md
- references/omx-compatibility.md

## Entry criteria

- Canonical documentation and harness contracts are complete
- Planner, Architect, and Critic evidence can be recorded in order

## Constraints

- Use Planner then Architect then Critic, followed by an explicit consensus gate
- When native role routing is used, require tracker-backed native_subagent Architect and Critic provenance from distinct sequential completed threads
- When the outcome or scope is unclear, use native Codex /plan, preserve the accepted result in the active ExecPlan, then use /goal
- Treat OMX as optional and interface-probed
- Use only explicit structured omx ultragoal steer mutations and preserve accepted, rejected, or deduped ledger evidence
- After a terminal aggregate Ultragoal run, use /goal clear only before a second aggregate run in the same Codex thread
- Leader alone owns Ultragoal state; Team workers return evidence only
- Ralph is an explicitly selected alternate execution loop
- When any product command category is unavailable, make the first milestone after consensus a blocking command bootstrap for real install, run/development, build, test, lint, format, type-check, integration, end-to-end, and authoritative ordered-gate commands before profile implementation

## Allowed writes

- docs/implementation/IMPLEMENTATION_BRIEF.md
- docs/implementation/EXECPLAN.md
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
- Concrete active ExecPlan governed by PLANS.md
- Planning artifacts plus tracker-backed native-subagent Architect, Critic, and consensus evidence when Ralplan is used
- Blocking product-command bootstrap milestone whenever any required command category is unavailable
- Native /goal handoff backed by the durable ExecPlan or deterministic sequential fallback
- Optional OMX CLI command only when compatibility probing passes

## Evidence and checks

- Planning evidence records planning_artifacts, ralplan_architect_review, ralplan_critic_review, and ralplan_consensus_gate with Architect-before-Critic approval provenance
- OMX probe records version, /goal clear lifecycle guidance, and the complete structured steering interface when requested
- Unsupported or missing OMX yields a neutral fallback
- Every unavailable product command is labeled unavailable, no replacement command is invented, and the active ExecPlan blocks profile implementation on a real ordered product gate
- The brief is executable without conversation history

## Stop or block when

- Consensus is not explicit
- OMX Ralplan role routing lacks documented leader proof or tracker-backed native subagent evidence
- OMX is requested but its version or interface is unsupported
- Product implementation would start before unavailable command categories and their authoritative ordered gate are bootstrapped
- A worker attempts to mutate leader-owned state

## Done when

- The handoff is implementation-ready under native Codex /goal with a current durable ExecPlan
- Any OMX state was created only by the supported CLI

## Runtime implementation boundary

- Do not implement or modify product runtime code. Produce the neutral brief, planning evidence, and optional CLI-created handoff only.
