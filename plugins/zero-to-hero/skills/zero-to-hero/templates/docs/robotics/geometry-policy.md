# Robotics geometry and robot-description policy

Status: `draft-required-input`

This file controls frames, kinematics, inertial data, visual/collision geometry, and URDF/SRDF/SDF derivation. It must be read with `docs/mechanical/cad-adapter.md`.

## STEP-first source-to-derived geometry policy

1. Approved mechanical requirements, dimension/tolerance ledger, and interface/frame definitions.
2. Project-owned parametric build123d source and assembly intent.
3. Immutable purchased-part STEP inputs with provenance and license evidence.
4. Explicitly generated primary STEP.
5. Generated URDF/SRDF/SDF and consumer-specific visual/collision meshes.
6. Renders and snapshots as review evidence only.

The STEP-first rule requires the smallest owning build123d source or controlled
purchased-part input to be resolved and validated before visual meshes,
collision meshes, URDF, SRDF, SDF, renders, or snapshots are derived. STEP
remains primary. STL, 3MF, GLB, images, topology, simplified collision meshes,
and fabrication-oriented files are derived. Do not hand-edit a derived artifact
to repair a source defect.

## earthtojake/text-to-cad routing

- Use `$step-parts` before placeholder geometry for named purchasable parts.
- Use the installed `$cad` workflow through `docs/mechanical/cad-adapter.md` for build123d source, explicit STEP generation, facts, frame, measurement, alignment, diff, and mandatory snapshots.
- Use the installed `$urdf`, `$srdf`, and `$sdf` skills for applicable robot descriptions.
- Use `$cad-viewer` only after its capability probe succeeds. The audited `0.3.9` package has a documented viewer command whose `agent:start` script was not present; record the probe failure and use deterministic inspection plus snapshot fallback.
- Do not restate or fork the upstream reusable skill methodology here.

## Link, joint, and frame registry

| Entity ID | Type | Parent | Child | Joint type | Axis in parent frame | Origin/transform source | Limits source | Consumer |
|---|---|---|---|---|---|---|---|---|
| `base_link` | `link` | `FRAME-WORLD` | `n/a` | `n/a` | `n/a` | `REQUIRED` | `n/a` | `URDF / SDF / simulation` |
| `REQUIRED_JOINT` | `joint` | `REQUIRED` | `REQUIRED` | `fixed / revolute / continuous / prismatic / other` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Rules:

- Frame names are stable and unique across CAD, URDF, SRDF, SDF, telemetry, calibration, and simulation.
- Origins, axes, rotation conventions, and units are explicit.
- Joint position, velocity, effort, acceleration, soft, and hard limits trace to an approved source.
- Mimic, closed-chain, transmission, floating, planar, or multi-DOF behavior is documented explicitly.
- Static transforms have an owner and validation evidence.

## Kinematic and assembly contract

| Chain/group | Root | Tip | Joint order | Degrees of freedom | Home/reference state | Singularities/limits | Validation |
|---|---|---|---|---:|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Define loop closures, coupled joints, calibration offsets, transmission ratios, compliance, backlash, hard stops, tool frames, sensor frames, and payload attachment frames.

## Inertial policy

| Link | Mass | Center of mass/frame | Inertia tensor | Source | Assumptions | Plausibility check | Status |
|---|---:|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `CAD / measured / datasheet / estimate` | `REQUIRED` | `REQUIRED` | `open` |

- Inertial values must be finite, physically plausible, use declared units, and be expressed in the documented inertial frame.
- Estimated density or mass distribution is labeled and assigned for human review.
- The tensor must satisfy symmetry and positive-definiteness expectations.
- Payload and configurable-tool inertials remain distinct from the base robot model.

## Visual and collision geometry policy

| Link/object | Visual source | Collision source | Simplification method | Units/origin | Fidelity target | Clearance impact | Validation |
|---|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Visual geometry may preserve appearance. Collision geometry must be deliberately simplified, conservative where required, stable under regeneration, and checked against critical clearances. Never reuse a visually convenient mesh as collision authority without review.

## Source-to-derived robot artifact map

| Artifact | Owning source/input | Generator | Explicit target | Consumer/check | Authority |
|---|---|---|---|---|---|
| `<part-or-assembly.step>` | build123d source/purchased inputs | `$cad` | exact path | facts, measure, alignment, diff, snapshot | generated primary |
| `<robot.urdf>` | robot-description source plus geometry map | `$urdf` | exact path | parser and target consumer | derived description |
| `<robot.srdf>` | semantic source plus approved URDF | `$srdf` | exact path | parser and planning consumer | derived semantics |
| `<robot.sdf>` | simulation source plus geometry map | `$sdf` | exact path | strict parser and simulator consumer | derived simulation description |
| `<visual-or-collision.glb|stl|3mf>` | STEP/source | audited CAD skill | exact path | consumer load and geometry checks | derived mesh |
| `<review.png>` | created/changed primary STEP | audited snapshot tool | exact path | human snapshot verdict | evidence |

## Exact audited generation interfaces

Replace placeholders with the resolved installed skill paths and repo-relative targets.

```txt
<CAD_PYTHON> <URDF_SKILL_DIR>/scripts/urdf <ROBOT_DESCRIPTION_SOURCE.py>=<ROBOT.urdf>
<CAD_PYTHON> <SRDF_SKILL_DIR>/scripts/srdf <SEMANTIC_SOURCE.py>=<ROBOT.srdf>
<CAD_PYTHON> <SDF_SKILL_DIR>/scripts/sdf <SIMULATION_DESCRIPTION_SOURCE.py>=<ROBOT.sdf> --gz-check <auto|required|never> --strict
```

Select `--gz-check` deliberately from the actual consumer environment. An unavailable required consumer is a skipped/blocked external integration, never a pass.

Robot-description generation does not replace consumer checks. Resolve and record exact project commands for:

```txt
<URDF_SCHEMA_OR_PARSER_CHECK>
<URDF_TARGET_CONSUMER_CHECK>
<SRDF_SCHEMA_OR_PARSER_CHECK>
<SRDF_PLANNING_CONSUMER_CHECK>
<SDF_SCHEMA_OR_PARSER_CHECK>
<SDF_TARGET_SIMULATOR_CHECK>
<MESH_URI_AND_RESOURCE_RESOLUTION_CHECK>
<FRAME_AND_JOINT_LIMIT_CHECK>
```

These are inert validation placeholders. They must not launch physical controllers or actuators.

## Validation ledger

| Check ID | Artifact/hash | Exact command/check | Expected | Actual | Evidence | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `ROBOT-GEO-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `not-run` |

Evidence must cover:

- units, coordinate frames, transforms, mesh origins, and resource resolution;
- link/joint names, types, axes, limits, and chain/group membership;
- mass, center of mass, inertia, and plausibility;
- visual versus collision fidelity and clearance impact;
- URDF/SRDF/SDF parser and consumer results;
- explicit STEP hashes, deterministic geometry checks, and mandatory snapshots;
- purchased-part and external asset provenance/licenses;
- assumptions, caveats, skipped external checks, and unresolved risk.

## Stop and done conditions

Stop if units, frames, dimensions, joint limits, inertials, geometry provenance, licenses, consumer availability, or safety assumptions are unresolved. Never accept a parser-only success as proof that kinematics, collision, dynamics, or planning semantics are correct.

Done requires all applicable descriptions to generate from source, pass their schema/parser and real consumer checks, resolve resources deterministically, trace to primary STEP/source, and retain human engineering and physical-action gates.
