# Mechanical / CAD Workflow

Use this only when the product has physical, mechanical, robotics, enclosure, mounting, manufacturing, or industrial design scope.

## Source-of-truth artifacts

```txt
docs/mechanical/
  requirements.md
  dimensions-and-tolerances.yaml
  material-and-finish.md
  manufacturing-process.md
  assembly.md
  bom.yaml
  interfaces-and-mounting.md
  mechanical-risk-register.md
  cad-generation-prompts.md
  cad-validation-policy.md
  test-fit-and-prototyping-plan.md
```

## Text-to-CAD workflow

When available, use earthtojake/text-to-cad or compatible CAD skills to produce STEP-first outputs. STEP should be the primary exchange format. Generate STL/3MF/GLB only as downstream or preview formats.

## Validation

Require:

```txt
units confirmed
coordinate system defined
critical dimensions listed
tolerances defined
materials defined
manufacturing assumptions stated
assembly constraints defined
clearance checks planned
fasteners/components linked to BOM
review images or viewer screenshots captured
```

## Robotics additions

If robotics is detected, also define:

```txt
URDF/SDF structure
link/joint naming
joint limits
inertial estimates
mounting interfaces
cable routing
sensor/actuator integration
simulation plan
```
