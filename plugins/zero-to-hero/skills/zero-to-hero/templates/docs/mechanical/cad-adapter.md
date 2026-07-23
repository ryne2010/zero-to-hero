# Local text-to-CAD adapter

Status: `draft-required-input`

This is a project-specific adapter to the installed `earthtojake/text-to-cad` skills. Keep reusable CAD methodology in the upstream skills; this file owns only project paths, targets, conventions, checks, evidence, and local decisions.

The audited compatibility baseline is `earthtojake/text-to-cad` tag `0.3.9`, published `2026-07-10`, resolving to commit [`fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423`](https://github.com/earthtojake/text-to-cad/commit/fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423). The release promotion records source commit `ac2659a1e7256b030a87dd4d45a37dcdccce6b45`. Before use, record the installed version/commit and probe the actual commands. A missing skill, mismatched version, or failed probe is blocking for CAD generation; do not fabricate equivalent runtime-owned interfaces.

## Safety and authority boundary

- These commands may create or inspect repository-local engineering artifacts only.
- They do not authorize fabrication, print starts, G-code generation, vendor uploads, deployment, energizing, or physical actuation.
- Parametric source is edited first. Derived output is regenerated to an explicit target.
- Never run directory-wide generation or silently overwrite an unreviewed authoritative input.

## Installed skill and command record

| Item | Required resolved value |
|---|---|
| Audited upstream baseline | `earthtojake/text-to-cad 0.3.9`; tag commit `fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423`; source commit `ac2659a1e7256b030a87dd4d45a37dcdccce6b45` |
| Installed version or commit | `REQUIRED` |
| CAD skill directory | `<CAD_SKILL_DIR>` |
| CAD viewer skill directory | `<CAD_VIEWER_SKILL_DIR>` |
| step-parts skill directory | `<STEP_PARTS_SKILL_DIR>` |
| URDF/SRDF/SDF skill directories | `<URDF_SKILL_DIR>`, `<SRDF_SKILL_DIR>`, `<SDF_SKILL_DIR>` |
| Repo-local Python | `<CAD_PYTHON>` |
| Capability-probe evidence | `<REPO_RELATIVE_EVIDENCE_PATH>` |

Pinned recovery install command, reference only and never automatic:

```txt
npx skills add https://github.com/earthtojake/text-to-cad/tree/0.3.9 --agent codex --skill cad --skill cad-viewer --skill step-parts --skill urdf --skill srdf --skill sdf --copy -y
```

Installing or changing skills requires explicit user approval and a trust review.

## Text-to-CAD routing contract

Resolve each CAD task through the narrow installed text-to-CAD skill that owns
the interface. Do not substitute an improvised generator when a required skill
or capability probe is unavailable.

| Task | Required route | Authoritative input | Explicit output/evidence | Blocking condition |
|---|---|---|---|---|
| Named purchasable component | `$step-parts` | reviewed manufacturer/catalog query | immutable STEP plus provenance, hash, units, origin, and license record | no trustworthy source or usage terms |
| Parametric part or assembly | `$cad` | project-owned build123d source and controlled STEP inputs | one explicit primary STEP target plus facts, measurements, and snapshot | unresolved units, frames, interfaces, or failed generation |
| Interactive visual review | `$cad-viewer` after a successful live probe | generated primary STEP and bounded review root | recorded reviewer verdict | missing `agent:start`, failed probe, or unbounded review root |
| Robot-description derivation | `$urdf`, `$srdf`, or `$sdf` as applicable | approved primary STEP and robot-description source | explicit derived target plus parser and real-consumer evidence | unresolved frame, joint, inertial, resource, or consumer contract |

Routing evidence must record the installed skill path and version, exact
file-targeted command, input and output hashes, exit status, and evidence path.
A failed required route is blocking; deterministic inspection and snapshot
review may document the failure but may not be reported as equivalent success.

## Project paths and conventions

| Role | Exact repo-relative path or convention |
|---|---|
| Parametric build123d source | `<CAD_SOURCE.py>` |
| Purchased-part STEP inputs | `<PURCHASED_PARTS_DIR>` |
| Primary explicit STEP target | `<PRIMARY_OUTPUT.step>` |
| Optional derived outputs | `<DERIVED_OUTPUT_DIR>` |
| Snapshot evidence | `<SNAPSHOT_OUTPUT.png>` |
| Baseline or approved comparison STEP | `<BASELINE.step>` |
| Geometry evidence report | `<GEOMETRY_EVIDENCE.md-or-json>` |
| Length/angle/mass units | `REQUIRED` |
| Global frame and datums | `docs/mechanical/interfaces-and-datums.md` |

The build123d source must expose named parameters, document units and frame conventions, preserve source-level assembly intent, and define `gen_step()` for the primary output. Purchased-part placement and simplified envelopes must be explicit source constructs.

## Canonical STEP-first loop

1. Resolve the CAD brief: dimensions, units, frames, materials, tolerances, interfaces, assumptions, and validation targets.
2. Invoke `$step-parts` for named purchasable parts before accepting placeholder geometry.
3. Edit the smallest owning build123d source with named parameters and assembly intent.
4. Generate the explicit primary STEP target.
5. Inspect facts, planes, positioning, frames, measurements, alignment, and diffs applicable to the change.
6. Create and review a snapshot for every created or visibly changed primary STEP.
7. Repair the smallest source, regenerate, and repeat failed checks.
8. Hand off to `$cad-viewer` only after its capability probe passes; otherwise use deterministic inspect plus snapshot evidence.
9. Report artifacts, exact checks run, assumptions, provenance/licenses, caveats, and unresolved risks.

## Exact audited command interfaces

Replace angle-bracket values with the resolved local paths from the table above. These commands are intentionally file-targeted.

Named purchased-part lookup and download:

```txt
<CAD_PYTHON> <STEP_PARTS_SKILL_DIR>/scripts/download_step_part.py "<PART_QUERY>" --download --out-dir <PURCHASED_PARTS_DIR>
```

Record the returned catalog ID, source URL, filename, retrieval date, units/origin, content hash, license/usage evidence, and chosen placement. Relevant audited selectors include `--id`, `--origin`, `--all`, `--filename`, `--overwrite`, `--limit`, `--page`, `--tag`, `--category`, `--family`, and `--standard`; use only the minimum needed.

Explicit STEP generation from source `gen_step()`:

```txt
<CAD_PYTHON> <CAD_SKILL_DIR>/scripts/step <CAD_SOURCE.py>=<PRIMARY_OUTPUT.step>
```

Optional `--kind part|assembly`, `--stl`, `--3mf`, and `--glb` outputs remain derived. `--force` requires explicit scoped replacement approval and pre-write provenance. Mesh tolerances must be recorded when mesh outputs are requested.

Baseline facts, planes, and positioning:

```txt
<CAD_PYTHON> <CAD_SKILL_DIR>/scripts/inspect refs <PRIMARY_OUTPUT.step> --facts --planes --positioning
```

Targeted geometry operations:

```txt
<CAD_PYTHON> <CAD_SKILL_DIR>/scripts/inspect frame <ENTRY> [<SELECTOR>]
<CAD_PYTHON> <CAD_SKILL_DIR>/scripts/inspect measure <ENTRY> --from <REF> --to <REF> [--axis x|y|z]
<CAD_PYTHON> <CAD_SKILL_DIR>/scripts/inspect align <ENTRY> --moving <REF> --target <REF> [--mode flush|center] [--offset <FLOAT>] [--axis x|y|z]
<CAD_PYTHON> <CAD_SKILL_DIR>/scripts/inspect diff <LEFT.step> <RIGHT.step>
```

Mandatory primary-STEP snapshot:

```txt
<CAD_PYTHON> <CAD_SKILL_DIR>/scripts/snapshot --input <PRIMARY_OUTPUT.step> --output <SNAPSHOT_OUTPUT.png> --appearance workbench
```

The audited snapshot interface also supports `--job <FILE|->` for a reviewed job description. Store the command, exit status, tool version, target hash, and snapshot path in the evidence report.

## Viewer capability gate

The audited `0.3.9` viewer documentation names:

```txt
npm --prefix <CAD_VIEWER_SKILL_DIR>/scripts/viewer run agent:start -- --host 127.0.0.1 --dir <ABSOLUTE_REVIEW_ROOT>
```

The audited package did not expose the referenced `agent:start` script. Treat `$cad-viewer` as unavailable until a live capability probe proves the installed package supports its documented interface. Do not label this handoff passed or invent a replacement viewer command. The deterministic fallback is:

1. run the applicable `inspect` operations;
2. generate the mandatory snapshot;
3. review the snapshot and record the verdict;
4. report the viewer handoff as unavailable with the exact probe evidence.

## Validation and evidence ledger

| Check ID | Target/hash | Exact command | Expected | Actual | Evidence path | Reviewer | Status |
|---|---|---|---|---|---|---|---|
| `CAD-FACTS-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `not-run` |

Required evidence for a created or visibly changed primary STEP:

- source and input hashes;
- explicit output target and post-generation hash;
- units, frame, shape kind, part/assembly count, and envelope facts;
- critical measurements and tolerances;
- mating alignment or clearance checks;
- baseline diff when an approved baseline exists;
- snapshot path plus human review verdict;
- regenerated derived-artifact list;
- purchased-part provenance and licenses;
- assumptions, caveats, and unresolved risks.

## Source repair and stop conditions

Repair the narrowest owning source parameter, transform, constraint, or assembly relation. Do not patch STEP, STL, 3MF, GLB, DXF, render, topology, URDF, SRDF, or SDF output by hand.

Stop when:

- required units, frames, dimensions, tolerances, materials, or interfaces are unresolved;
- a purchased-part model lacks trustworthy provenance or license evidence;
- the installed skill/version/interface probe fails;
- generation, inspection, measurement, alignment, diff, or snapshot fails;
- a snapshot exposes a visible defect or unexplained change;
- physical or manufacturing approval would be required.

## Done when

- Project paths and the installed/audited command record are resolved.
- Named purchased parts were sourced or explicitly documented as bounded placeholders.
- Parametric source and source-level assembly intent are authoritative.
- Explicit STEP generation and all applicable deterministic checks pass.
- Mandatory snapshot review passes.
- Viewer status is honestly recorded, including deterministic fallback when unavailable.
- Evidence, provenance, licenses, assumptions, caveats, and unresolved risks are complete.
- Human engineering and physical-authorization gates remain unbypassed.
