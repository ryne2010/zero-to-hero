# Robotics requirements

Status: `draft-required-input`

This document defines implementation-ready robotics engineering intent. It does not provide product runtime code and does not authorize fabrication, flashing, deployment, energizing, motion, or physical actuation.

## System scope

| Field | Required value |
|---|---|
| Robot/system name | `REQUIRED` |
| Intended task and users | `REQUIRED` |
| Operating environment | `REQUIRED` |
| Included subsystems | `REQUIRED` |
| External systems and operators | `REQUIRED` |
| Explicit non-goals | `REQUIRED` |
| Autonomy level and human supervision | `REQUIRED` |
| Safety classification or unresolved regulatory questions | `REQUIRED` |

## Authoritative supporting documents

- `docs/mechanical/requirements.md`
- `docs/mechanical/dimensions-and-tolerances.yaml`
- `docs/mechanical/interfaces-and-datums.md`
- `docs/mechanical/cad-adapter.md`
- `docs/firmware/requirements.md`
- `docs/robotics/geometry-policy.md`
- `docs/robotics/simulation-and-bring-up.md`

If a geometry, frame, joint, limit, interface, or safety assumption conflicts across these sources, stop and resolve it before generation.

## Geometry and assembly prerequisites

Before creating robot descriptions or simulation assets:

1. Define units, global frame, link/joint frame convention, datums, and mesh origins.
2. Resolve critical dimensions, tolerances, travel limits, clearances, cable/service envelopes, and assembly order.
3. Route named purchased components through `$step-parts`; record provenance and license evidence.
4. Route repo-owned geometry through the installed `earthtojake/text-to-cad` CAD skill and `docs/mechanical/cad-adapter.md`.
5. Keep build123d source authoritative and generate explicit STEP targets.
6. Complete deterministic facts, measurement, alignment, diff, and mandatory snapshot evidence for created or visibly changed primary STEP.
7. Approve the source-to-derived map before deriving visual/collision meshes or URDF/SRDF/SDF.

Unknown geometry prerequisites are blocking. A bounding box or render is not sufficient dimensional authority.

## Operational modes and state contracts

| Mode/state | Entry condition | Allowed behavior | Forbidden behavior | Exit condition | Timeout/failure response | Human role |
|---|---|---|---|---|---|---|
| `SAFE_UNPOWERED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |
| `SIMULATION_ONLY` | `REQUIRED` | `REQUIRED` | `physical effects` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Define boot, initialization, calibration, idle, commanded operation, degraded, fault, emergency, shutdown, maintenance, and recovery states when applicable. Safe-state behavior must be explicit for power loss, communications loss, stale commands, sensor disagreement, actuator fault, limit violation, and software restart.

## Functional requirements

| ID | Requirement | Operating mode | Input/precondition | Expected result | Timing/accuracy | Verification | Status |
|---|---|---|---|---|---|---|---|
| `ROBOT-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `simulation / analysis / inspection / human review` | `open` |

Requirements must cover, when applicable:

- workspace, payload, reach, speed, acceleration, repeatability, accuracy, and duty cycle;
- sensor field of view, range, resolution, rate, calibration, synchronization, and failure behavior;
- actuator effort, limits, feedback, thermal behavior, brakes, compliance, and safe state;
- control ownership, command validity, arbitration, timeouts, and stale-data handling;
- localization, mapping, planning, collision avoidance, perception confidence, and operator override;
- communications, clocks, frame timestamps, logs, telemetry, replay, and data retention;
- maintenance access, inspection, calibration, transport, storage, and recovery.

## Hardware and software interface ledger

| Interface ID | Producer | Consumer | Physical/logical medium | Data or signal contract | Rate/timing | Units/frame | Fault behavior | Owner |
|---|---|---|---|---|---|---|---|---|
| `RIF-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Every physical connector must trace to the mechanical datum/interface and firmware pin/channel identity. Every pose, twist, wrench, joint, image, point cloud, or sensor message must declare units, frame, timestamp policy, and invalid/stale semantics.

## BOM, external geometry, provenance, and licenses

| Item ID | Manufacturer/part | Function | Quantity | Source/catalog URL | Geometry source/revision/hash | Software/data/license terms | Approved substitute policy | Owner |
|---|---|---|---:|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `1` | `REQUIRED` | `REQUIRED_OR_NOT_APPLICABLE` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Record provenance for purchased-part STEP, meshes, robot descriptions, calibration data, datasets, maps, plugins, and simulation assets. Unknown origin, units, frame convention, revision, or license is blocking.

## Safety constraints and failure modes

| Hazard/failure | Initiating cause | Detection | Automatic safe response | Human response | Recovery preconditions | Validation evidence | Residual-risk owner |
|---|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Define boundaries for speed, force, torque, temperature, voltage, workspace, separation, communications, stale data, localization confidence, collision confidence, and operator access. Document emergency-stop assumptions without claiming a software-only mechanism is a certified safety function.

## Human engineering and physical authorization

The generated scaffold may prepare specifications, simulations, source models, robot descriptions, and evidence only.
The human engineering review gate and physical action authorization gate are
separate blocking decisions and require independently recorded evidence.

A separate explicit human authorization is required before:

- fabrication, assembly, procurement, or modification of physical hardware;
- flashing or updating a physical controller;
- energizing sensors, actuators, motors, heaters, batteries, pressure, or mains-connected equipment;
- deploying to a robot or shared environment;
- starting motion, calibration motion, homing, manipulation, or autonomous behavior;
- bypassing an interlock, limit, guard, stop, or supervision requirement.

The authorization record must identify qualified reviewers, exact scope, environment, evidence, conditions, stop authority, and unresolved risks.

## Done when

- System scope, modes, requirements, interfaces, hazards, and safe-state behavior are resolved.
- Geometry prerequisites, mechanical interfaces, frames, joint limits, and source-derived ownership are complete.
- BOM/external assets include provenance, revisions/hashes, units/frames, and license evidence.
- Simulation, telemetry, failure injection, recovery, and staged bring-up evidence are defined.
- URDF/SRDF/SDF policies and consumer checks are complete where applicable.
- Human engineering and physical-action gates are explicit and cannot be mistaken for approval.
