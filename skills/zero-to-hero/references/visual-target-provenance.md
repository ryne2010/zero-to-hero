# Visual target provenance

Generated images, screenshots, Figma frames, CAD renders, and diagrams are visual evidence. They become canonical only after approval and deconstruction.

Recommended metadata:

```yaml
visual_id: dashboard.desktop
status: canonical
source:
  kind: image_generation | figma | screenshot | hand_drawn | cad_render
  file: docs/ui/visual-assets/dashboard.desktop.png
  generator_or_tool: optional
  approved_by_user: true
  approved_at: ISO-8601-or-session-note
requires:
  - visual_deconstruction
  - route_capsule
  - interaction_contract
  - accessibility_notes
```

Behavior implied by a visual target is `inferred` until recorded in the decision ledger or route contract.
