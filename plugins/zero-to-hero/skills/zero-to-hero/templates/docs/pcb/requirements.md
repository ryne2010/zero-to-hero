# PCB and electronics requirements

Status: `draft-required-input`

This document defines implementation-ready electrical engineering intent. It contains no product runtime code and does not authorize board fabrication, upload, ordering, assembly, flashing, energizing, RF transmission, or connection to real equipment.

## Product and board scope

| Field | Required value |
|---|---|
| Product/board name | `REQUIRED` |
| Board revision strategy | `REQUIRED` |
| Electrical function | `REQUIRED` |
| Operating environment | `REQUIRED` |
| Supply sources and limits | `REQUIRED` |
| External equipment/users | `REQUIRED` |
| Size/mechanical constraints | `REQUIRED` |
| Safety/compliance questions | `REQUIRED_OR_NONE_WITH_RATIONALE` |
| EDA tool and audited version | `REQUIRED` |

## Electrical architecture and block diagram

| Block ID | Function | Inputs | Outputs | Voltage/power domain | Interfaces | Critical constraints | Owner |
|---|---|---|---|---|---|---|---|
| `BLOCK-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Document domain crossings, isolation, grounding, shielding, clocking, reset, programming/debug, test access, and off-board connections.

## Power tree and budget

| Rail ID | Source | Nominal/range | Max load | Startup/inrush | Protection | Sequencing | Consumers | Margin/evidence |
|---|---|---|---:|---|---|---|---|---|
| `PWR-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Include normal, peak, startup, sleep, fault, reverse, brownout, short, and thermal assumptions. Battery, mains, high-voltage, high-current, charging, and hazardous-energy scope requires qualified domain review.

## I/O, connector, and pin map

| Interface ID | Connector/refdes | Pin | Signal | Direction | Voltage/protocol | Default/safe state | Peer | Mechanical interface | Firmware identity |
|---|---|---:|---|---|---|---|---|---|---|
| `PCB-IF-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

The input/output map binds every I/O signal to one connector pin, component
endpoint, electrical and protocol contract, safe state, firmware identity, and
mechanical interface. Shared pins, alternate functions, no-connects, test-only
signals, and board-revision differences require explicit rows or compatibility
rules rather than implicit schematic knowledge.

Record keying, mating cycle, retention, pin-1 convention, hot-plug, ESD/EFT, overvoltage, pull/termination, cable/shield, creepage/clearance, and misconnection behavior.

## Component selection, BOM, provenance, and licensing

| Item/refdes | Manufacturer/part number | Function | Critical ratings | Lifecycle/availability | Approved substitute policy | Datasheet/source | Footprint/symbol/model provenance | License/usage evidence | Owner |
|---|---|---|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Rules:

- Verify ratings, tolerances, derating, temperature, package, pinout, polarity, and revision.
- Record source, retrieval date, revision or content hash, and license/usage terms for symbols, footprints, 3D models, reference designs, and libraries.
- Treat unverified community assets as untrusted inputs until reviewed.
- Substitutions must assess electrical, firmware, mechanical, sourcing, compliance, and test impact.

## Schematic constraints and review

| Constraint ID | Nets/components | Requirement | Rationale/source | Review/check | Evidence | Status |
|---|---|---|---|---|---|---|
| `SCH-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `open` |

Review power, decoupling, bias, reset, boot straps, clocks, analog references, protection, terminations, unused pins, test points, labels, net classes, isolation, and design-rule assumptions.

## Layout, stackup, SI/PI, thermal, DFM, and DFT constraints

| Constraint ID | Region/net/class | Requirement | Layer/stackup | Clearance/geometry | Verification | Owner |
|---|---|---|---|---|---|---|
| `LAYOUT-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Document:

- board outline, thickness, layer count, materials, copper, impedance assumptions, finish, and tolerances;
- placement keep-outs, orientation, return paths, stitching, high-current/thermal paths, sensitive analog/RF areas;
- differential pairs, impedance, length/skew, via, plane, creepage, clearance, isolation, and EMC assumptions;
- panelization, fiducials, tooling, assembly clearances, test access, rework, inspection, and marking;
- mechanical datums, mounting, enclosure, connector, and cable constraints.

Supplier-specific fabrication values remain assumptions until reviewed and approved by the responsible engineer and supplier.

### DFM, DFT, and test-jig plan

Design-for-manufacture and design-for-test evidence must trace each critical
rail, interface, programmed device, safety boundary, and inaccessible node to a
reviewable inspection or fixture strategy.

| Jig/coverage ID | Requirement or node | Access feature and datum | Isolated stimulus | Expected measurement/tolerance | Fault containment | Coverage evidence | Owner/reviewer | Status |
|---|---|---|---|---|---|---|---|---|
| `PCB-JIG-001` | `REQUIRED` | `REQUIRED_TEST_POINT_OR_CONNECTOR` | `REQUIRED_INERT_OR_SEPARATELY_AUTHORIZED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `not-run` |

The test-jig plan must define fixture alignment, connector life, test-point
geometry, probe clearance, isolation, current and voltage limits, calibration,
known-good references, false-pass/false-fail handling, serial-number and result
traceability, and the coverage gap for every untested node. DFM review must
cover supplier capabilities, panelization, tooling, assembly access, inspection
methods, and rework assumptions; DFT review must cover observability,
controllability, boundary conditions, and safe failure containment.

This scaffold records the plan and inert evidence only. Building or connecting
a jig, applying power, programming a device, transmitting RF, or probing an
energized board requires separately reviewed instructions and explicit human
authorization for the exact equipment and limits.

## Inert validation commands and evidence

| Check | Exact resolved command | Expected result | Evidence path | Status |
|---|---|---|---|---|
| Schematic syntax/project check | `<PCB_SCHEMATIC_CHECK_COMMAND>` | no unresolved structural error | `REQUIRED` | `not-run` |
| ERC | `<PCB_ERC_COMMAND>` | reviewed findings and justified waivers | `REQUIRED` | `not-run` |
| PCB syntax/project check | `<PCB_LAYOUT_CHECK_COMMAND>` | no unresolved structural error | `REQUIRED` | `not-run` |
| DRC | `<PCB_DRC_COMMAND>` | reviewed findings and justified waivers | `REQUIRED` | `not-run` |
| BOM consistency | `<PCB_BOM_CONSISTENCY_COMMAND>` | schematic/layout/BOM agreement | `REQUIRED` | `not-run` |
| Authoritative local done gate | `<PCB_DONE_COMMAND>` | all inert checks and reviews pass | `REQUIRED` | `not-run` |

Resolve commands from the selected EDA tool/version. These commands must be validation-only and must not generate or upload fabrication packages.

Waivers must identify rule, exact location/scope, rationale, evidence, reviewer, expiry/revisit condition, and residual risk.

## Fabrication and assembly output policy

Potential Gerber, drill, IPC, pick-and-place, assembly, stencil, BOM, drawing, or archive outputs are derived from reviewed source. This scaffold:

- defines expected output ownership and validation;
- may document a future downstream handoff;
- does not generate those outputs;
- does not upload or order anything;
- does not label any package fabrication-ready.

| Derived output family | Owning source | Expected downstream validation | Human approver | Authorization status |
|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `not-authorized` |

## Test, fixture, and bring-up intent

| Test ID | Requirement/interface | Inert fixture/simulation | Stimulus | Expected observation | Fault/limit case | Evidence |
|---|---|---|---|---|---|---|
| `PCB-TEST-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Define inspection, continuity/isolation intent, current-limited power assumptions, rail validation, programming/debug access, interface loopbacks, boundary tests, thermal observation, and failure containment without embedding commands that energize or control real hardware.

## Hazards and review gates

| Hazard | Cause | Design control | Verification | Qualified reviewer | Residual risk |
|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Human engineering review is mandatory before fabrication-output generation, vendor upload, ordering, assembly, flashing, energizing, connecting hazardous sources, RF transmission, or deployment.

## Done when

- Architecture, power, I/O, connectors, components, constraints, interfaces, and board revisions are resolved.
- BOM/assets have provenance, hashes/revisions, ratings, availability, substitution, and license evidence.
- Exact inert project, ERC, DRC, and consistency checks pass with reviewed waivers.
- Mechanical/firmware cross-domain identities agree.
- Fabrication outputs remain derived and explicitly unauthorized.
- Test intent, hazards, qualified review, and physical-action gates are complete.
- No runtime code or real-world action command is generated.
