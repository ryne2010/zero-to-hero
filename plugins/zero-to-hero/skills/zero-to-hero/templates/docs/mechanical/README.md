# Mechanical source-of-truth pack

This directory defines implementation-ready mechanical engineering intent. It does not authorize fabrication, procurement, printer starts, machine operation, uploads, or any other physical action.

## Read order and authority

1. `requirements.md` — scope, materials, manufacturing assumptions, BOM provenance, risks, and authorization gates.
2. `dimensions-and-tolerances.yaml` — machine-readable units, dimensions, tolerances, stack-ups, and measurement targets.
3. `interfaces-and-datums.md` — interfaces, datums, coordinate frames, unit conversions, and assembly prerequisites.
4. `cad-adapter.md` — project-local adapter to the installed `earthtojake/text-to-cad` skills, source-to-derived policy, exact inert commands, and validation evidence.

If these files disagree, stop and record the conflict. Do not infer a dimension, tolerance, material, datum, frame, or physical interface from a render or derived mesh.

## Source hierarchy

- Parametric build123d Python is the editable geometry source.
- Named purchased-part STEP files are controlled external inputs with provenance and license evidence.
- STEP is the primary generated exchange artifact.
- STL, 3MF, GLB, DXF, renders, topology, and fabrication-oriented files are derived artifacts.
- Images are review evidence, never dimensional authority.

## Completion boundary

This pack is complete only when required fields are resolved, the source-to-derived map is traceable, deterministic geometry checks and snapshot review are recorded, and a qualified human engineer has reviewed assumptions that affect physical safety or manufacturability.
