# Prompt: Hardware, robotics, firmware, mechanical, and PCB pack

<!-- Generated from references/contract-graph.yaml::hardware_pack. Do not edit by hand. -->

Use the `zero-to-hero` skill and follow this contract exactly.

## Applicability

- profiles_any: firmware-iot, mechanical-product, pcb-electronics, robotics-product

## Goal

- Create substantive, profile-specific engineering documentation and validation adapters while preserving human control over physical actions.

## Context and required reads

- Selected hardware profile YAML files
- references/mechanical-cad-workflow.md
- references/firmware-iot-robotics-workflow.md
- references/pcb-workflow.md
- references/text-to-cad-compatibility.md when geometry is in scope

## Entry criteria

- At least one hardware profile is selected
- Units, coordinate conventions, interfaces, and physical safety boundaries are approved

## Constraints

- Use earthtojake/text-to-cad as the canonical adapter for applicable geometry
- Keep STEP primary and treat mesh, image, and fabrication formats as derived
- Require human engineering review and separate authorization for real-world effects

## Allowed writes

- docs/hardware/
- docs/firmware/
- docs/mechanical/
- docs/pcb/
- docs/robotics/

## Forbidden writes

- Firmware runtime source
- CAD source or derived geometry in the target product
- Fabrication release files
- Printer, upload, deployment, energizing, or actuation commands
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

- Requirements, tolerances, materials, interfaces, datums, frames, and unit ledgers
- Source-to-derived artifact and provenance maps
- Simulation, bring-up, telemetry, failure-mode, and safety contracts
- Human engineering and physical authorization gates

## Evidence and checks

- Text-to-CAD routing and audited interface are explicit when applicable
- STEP generation target, deterministic checks, and mandatory snapshot review are specified
- URDF, SRDF, or SDF consumer checks are specified when applicable

## Stop or block when

- Physical safety, units, tolerances, materials, or interfaces are unresolved
- A real-world effect would occur
- Required upstream CAD tooling is missing or incompatible

## Done when

- Engineering artifacts are reviewable without being marked fabrication-approved
- Every physical output has provenance, checks, caveats, and a human authorization gate

## Runtime implementation boundary

- Do not implement product firmware, CAD, PCB, robotics runtime, or initiate any physical action. Prepare documentation and validation handoffs only.
