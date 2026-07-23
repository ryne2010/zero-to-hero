# Mechanical requirements

Status: `draft-required-input`

This document specifies mechanical engineering intent for later implementation. It must not contain product runtime code or be treated as authorization to fabricate, purchase, upload, print, machine, assemble, energize, deploy, or actuate anything.

## Product and physical scope

| Field | Required value |
|---|---|
| Product or assembly | `REQUIRED` |
| Intended users and environment | `REQUIRED` |
| Mechanical function | `REQUIRED` |
| Included parts and assemblies | `REQUIRED` |
| Explicit exclusions | `REQUIRED` |
| Service life and duty cycle assumptions | `REQUIRED` |
| Storage and operating environment | `REQUIRED` |
| Human-contact or safety-critical surfaces | `REQUIRED` |
| Applicable standards or regulatory questions | `REQUIRED_OR_NONE_WITH_RATIONALE` |

Unresolved physical scope is blocking. Record assumptions as assumptions; do not silently convert them into requirements.

## Engineering invariants

- Units, handedness, origin, axes, datums, and frame transforms are explicit.
- Critical dimensions and tolerances are owned by `dimensions-and-tolerances.yaml`.
- Mating geometry is owned by `interfaces-and-datums.md`.
- Editable geometry comes from named source parameters and assembly intent.
- Purchased parts are looked up through `$step-parts` before placeholder geometry is accepted.
- STEP is primary. STL, 3MF, GLB, DXF, images, and fabrication-oriented files are derived.
- Derived files are regenerated from source and are never hand-edited as the authoritative fix.
- Every created or visibly changed primary STEP receives deterministic checks and snapshot review.
- Physical actions require a separate, explicit, human-authorized downstream procedure.

## Functional and physical requirements

| ID | Requirement | Source or rationale | Verification method | Acceptance value | Status |
|---|---|---|---|---|---|
| `MECH-001` | `REQUIRED` | `REQUIRED` | `inspect / measure / analysis / human review` | `REQUIRED` | `open` |

Requirements must cover, when applicable:

- load paths, stiffness, strength, fatigue, shock, vibration, and stability;
- envelope, mass, center of mass, balance, range of motion, and keep-out volumes;
- thermal expansion, heat paths, ventilation, sealing, ingress, corrosion, and UV exposure;
- fasteners, inserts, adhesives, retention, service access, cable routing, and strain relief;
- ergonomic clearances, pinch/crush/sharp-edge risks, accessibility, and maintenance;
- manufacturing variation, assembly sequence, inspection access, and repairability.

## Materials, finishes, and manufacturing assumptions

| Part or family | Material specification | Candidate process | Finish or treatment | Critical property | Assumption/evidence | Human owner | Status |
|---|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED_OR_NONE` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `open` |

For each candidate process, document:

- minimum feature, wall, radius, draft, overhang, support, and tool-access assumptions;
- shrinkage, warp, anisotropy, grain or layer direction, and expected process variation;
- surface, flatness, perpendicularity, concentricity, and inspection assumptions;
- stock form, availability, substitution, finishing, cleaning, and compatibility constraints;
- whether the assumption is supplier-confirmed, standards-backed, calculated, tested, or unresolved.

No manufacturing assumption is an approval. A qualified reviewer must select and approve the actual process and material specification.

## BOM, purchased parts, provenance, and licensing

| Item ID | Make/buy | Manufacturer and part number | Quantity | Source URL/catalog | STEP source and revision/hash | License or usage terms | Substitute policy | Evidence owner |
|---|---|---|---:|---|---|---|---|---|
| `REQUIRED` | `make / buy` | `REQUIRED` | `1` | `REQUIRED` | `REQUIRED_OR_NOT_APPLICABLE` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Rules:

1. Use `$step-parts` for named purchasable components before creating simplified geometry.
2. Record vendor/manufacturer identity, catalog identifier, retrieval date, revision or content hash, units, origin convention, and license/usage evidence.
3. Keep imported STEP immutable. Adapt placement or interfaces in repo-owned parametric source.
4. If no trustworthy model exists, label simplified geometry as a non-manufacturing placeholder and record its dimensional limits.
5. Record availability, lifecycle, approved alternatives, and fit-impact for substitutions.

## Source-to-derived artifact map

| Artifact | Role | Owning source/input | Generator or external source | Regeneration target | Validation | Authority |
|---|---|---|---|---|---|---|
| `<repo-relative build123d source.py>` | editable geometry | product requirements and ledgers | project-owned | `<primary.step>` | import, facts, measure, snapshot | authoritative source |
| `<purchased-part.step>` | controlled external input | manufacturer/catalog record | `$step-parts` or approved vendor | immutable input | units, origin, envelope, provenance | authoritative external input |
| `<primary.step>` | primary exchange | build123d source and purchased inputs | audited CAD skill | explicit target | facts, planes, positioning, measure, align, diff, snapshot | generated primary |
| `<derived.stl|3mf|glb|dxf>` | downstream representation | primary STEP/source | audited CAD skill | explicit target only | consumer-specific checks | derived |
| `<review.png>` | visual evidence | primary STEP | audited snapshot tool | explicit target | human snapshot review | evidence only |

Every row must name an owner and a deterministic regeneration path. Stale outputs remain unresolved until explicitly removed or reconciled; generators must not silently delete them.

## Assembly, service, and inspection

| Assembly step | Preconditions | Parts/tools | Datum or interface | Torque/fit/adhesive assumption | Inspection evidence | Rework path |
|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Document assembly order, captive parts, access constraints, alignment features, tolerance-sensitive steps, calibration dependencies, and disassembly/service limitations.

## Risks and failure modes

| Hazard or failure mode | Cause | Effect | Detection | Design mitigation | Validation | Residual risk owner |
|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Escalate battery, pressure, structural, lifting, rotating machinery, medical, automotive, aerospace, RF, high-temperature, mains, human-support, or other safety-critical scope to a qualified domain engineer.

## Human engineering and physical authorization gates

The documentation and CAD workflow may prepare and validate artifacts only.
The human engineering review gate and fabrication authorization gate are
separate blocking decisions; neither may be inferred from generated evidence.

Separate explicit human authorization is required before:

- procurement or substitution of safety-relevant parts;
- fabrication, machining, printing, cutting, forming, or assembly;
- upload to a vendor or manufacturing service;
- energizing hardware, running machinery, field deployment, or physical actuation;
- acceptance of any design affecting human safety, compliance, or regulated use.

Authorization records must identify reviewer, scope, evidence reviewed, date, decision, conditions, and unresolved risks. Absence of a rejection is not approval.

## Done when

- All `REQUIRED` fields are resolved or recorded as blocking decisions.
- `dimensions-and-tolerances.yaml` validates and covers every critical requirement.
- `interfaces-and-datums.md` defines every mating interface and frame.
- Materials, processes, BOM entries, provenance, licenses, substitutions, and risks are reviewable.
- `cad-adapter.md` records the installed/audited skill interfaces and exact project paths.
- Source-to-derived ownership and regeneration are complete.
- Deterministic geometry evidence and mandatory STEP snapshots are recorded.
- Human engineering and physical-authorization gates remain explicit and unbypassed.
