# Canonical Docs Structure

Use a docs-first source-of-truth structure. Keep canonical documents authoritative and remove intermediate iteration artifacts during cleanup.

```txt
docs/
  00-meta/
    canonical-handoff.md
    source-of-truth-map.yaml
    feature-index.yaml
    implementation-boundaries.md
    cleanup-policy.md

  product/
    vision.md
    personas.md
    glossary.md
    non-goals.md
    success-metrics.md
    competitors-and-market.md

  stories/
    story-index.yaml
    workflows/
    edge-cases/

  architecture/
    system-overview.md
    local-mode.md
    production-mode.md
    data-model.md
    event-model.md
    state-machines/
    decisions/

  contracts/
    api/
    database/
    permissions/
    events/

  ui/
    README.md
    DIRECTION.md
    visual-assets/
    frontend-builder-context.md
    frontend-parity-system/
    application-specs/

  product-execution/
    app-usability-contract.md
    action-binding-matrix.yaml
    workflow-transactions/
    dataflows/
    forms/
    scenarios/
    runtime-evidence/
    traceability/
    local-simulators/
    negative-paths/
    role-walkthroughs/
    observability/
    local-product-done-gate.md

  hardware/
  mechanical/
  pcb/
  firmware/
  robotics/

  production-readiness/
    local-to-production-delta.md
    live-provider-gates.md
    observability-readiness.md
    security-readiness.md

  runbooks/
  quality/
```

## Required meta docs

- `source-of-truth-map.yaml` tells agents which docs govern which surfaces.
- `feature-index.yaml` lists canonical features only.
- `canonical-handoff.md` states final hard decisions and boundaries.
- `cleanup-policy.md` defines what must be removed before handoff.
