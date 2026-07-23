# Mechanical interfaces, datums, frames, and units

Status: `draft-required-input`

This file is the interface-control source for mating geometry, datums, coordinate frames, and unit conversion. It must agree with `dimensions-and-tolerances.yaml` and the named parameters in CAD source.

## Global convention

| Field | Required value |
|---|---|
| Length unit | `REQUIRED` |
| Angle unit | `degrees` unless explicitly approved otherwise |
| Mass unit | `REQUIRED` |
| Handedness | `REQUIRED` |
| Global origin | `REQUIRED` |
| +X / +Y / +Z meaning | `REQUIRED` |
| Rotation order/convention | `REQUIRED` |
| Gravity direction when applicable | `REQUIRED_OR_NOT_APPLICABLE` |

Never infer a frame from how a model appears in a viewer.

## Datum scheme

| Datum ID | Type | Owning part | Geometric definition | Purpose | Establishment/inspection method | Source reference |
|---|---|---|---|---|---|---|
| `DATUM-A` | `plane / axis / point` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED_PARAMETER_OR_FACE_RULE` |

Primary, secondary, and tertiary datums must constrain the intended degrees of freedom without over-constraining assembly.

## Interface-control ledger

| Interface ID | Side A | Side B | Mating references | Constraint/DOF | Fastener or retention | Fit/seal/clearance | Load path | Assembly prerequisite | Verification |
|---|---|---|---|---|---|---|---|---|---|
| `IFACE-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

For every interface, specify:

- nominal location and orientation;
- allowed translation and rotation;
- minimum/maximum clearance or interference;
- thread, insert, fastener, adhesive, gasket, connector, or retention assumptions;
- assembly approach direction and tool/access envelope;
- cable, hose, thermal, optical, acoustic, or fluid constraints;
- datum transfer and tolerance-stack ownership;
- inspection references that survive regeneration.

## Coordinate-frame registry

| Frame ID | Parent frame | Origin definition | Orientation definition | Units | Owning artifact/source | Consumer | Validation |
|---|---|---|---|---|---|---|---|
| `FRAME-WORLD` | `none` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `CAD / URDF / SDF / analysis` | `REQUIRED` |

Frame names must remain stable across CAD, URDF, SRDF, SDF, simulation, firmware interface documents, and measurement evidence. Record every transform rather than relying on viewer placement.

## Unit-conversion register

| Conversion ID | Source | Target | Exact factor/reference | Affected dimensions/interfaces | Verification |
|---|---|---|---|---|---|
| `UNIT-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Conversions are explicit at boundaries. A source model with unknown units is blocking.

## Assembly prerequisites

| Assembly or interface | Required upstream parts | Required verified dimensions | Alignment order | Temporary fixtures | Inspection before continuation | Blocking unresolved items |
|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED_OR_NONE` | `REQUIRED` | `REQUIRED_OR_NONE` |

## Cross-domain interface handoff

When electronics, firmware, or robotics is in scope, record:

- PCB mounting envelope, keep-outs, connector access, grounding, shielding, and thermal paths;
- sensor/actuator axes, zero positions, hard stops, cable routing, and strain relief;
- firmware-visible pin or channel identity associated with a physical connector;
- robot link/joint frames and mesh origins;
- calibration or service fixtures that depend on datums.

## Verification and done criteria

- Every mating pair has one interface ID and named references on both sides.
- Every coordinate frame has a parent, origin, orientation, units, owner, and consumer.
- All critical interface values trace to the dimension ledger.
- Tolerance stacks identify their datum scheme and inspection method.
- CAD facts, positioning, measurement, alignment, or diff evidence covers each critical interface.
- Human engineering review is recorded before any physical authorization.
