# PCB / Electronics Workflow

Default to a KiCad-first open-source workflow when no other EDA stack is specified.

## Source-of-truth artifacts

```txt
docs/pcb/
  requirements.md
  block-diagram.md
  power-tree.yaml
  io-map.yaml
  connector-map.yaml
  component-selection.md
  bom-policy.md
  schematic-review-checklist.md
  layout-constraints.md
  stackup-and-fab-notes.md
  dfm-dft-checklist.md
  firmware-bringup-plan.md
  test-jig-plan.md
  fabrication-output-policy.md
```

## Review gates

No PCB should proceed to fabrication without:

```txt
schematic review
ERC review
PCB DRC review
power budget review
connector/pinout review
BOM availability review
fabrication outputs review
human signoff
```

## KiCad CLI expectations

When KiCad is used, the repo should support automated checks and output generation where practical:

```txt
kicad-cli sch erc
kicad-cli pcb drc
kicad-cli pcb export gerbers
kicad-cli pcb export drill
kicad-cli pcb export position
```

Do not automatically order boards. Generate evidence and require human review.
