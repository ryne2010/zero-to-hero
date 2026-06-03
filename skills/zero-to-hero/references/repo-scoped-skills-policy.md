# Repo-scoped skills policy

Generate repo-scoped skills only when they provide repeatable implementation workflows.

Default generated skills should be limited to 3-5 unless the user requests more.

Good examples:

```txt
.agents/skills/frontend-parity/
.agents/skills/product-usability/
.agents/skills/local-mode-verification/
.agents/skills/runtime-evidence/
.agents/skills/final-local-product-review/
```

Generate hardware-specific skills only when applicable:

```txt
.agents/skills/mechanical-cad/
.agents/skills/pcb-review/
.agents/skills/firmware-bringup/
.agents/skills/robotics-simulation/
```

Do not create overlapping skills with duplicate scope. Each skill must have a short trigger-friendly description and a narrow workflow.
