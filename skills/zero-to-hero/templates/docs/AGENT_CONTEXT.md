# Agent context router

Read this before implementation planning. Do not read the entire docs tree unless the task requires it.

## Source of truth

1. `AGENTS.md`
2. `CODEX.md`
3. `FINAL_HANDOFF.md`
4. `docs/00-meta/source-of-truth-map.yaml`
5. task-specific docs selected by the source-of-truth map

## Task-specific routers

- UI tasks: `docs/ui/FRONTEND_CONTEXT.md`
- Mobile tasks: `docs/mobile/requirements.md`
- Desktop tasks: `docs/desktop/requirements.md`
- API tasks: `docs/api/requirements.md`
- CLI tasks: `docs/cli/requirements.md`
- AI tasks: `docs/ai/requirements.md`
- Data/ML tasks: `docs/data/requirements.md`
- Infrastructure tasks: `docs/infra/requirements.md`
- Local product completion: `docs/product-execution/LOCAL_PRODUCT_CONTEXT.md`
- Firmware: `docs/firmware/requirements.md`
- Mechanical/CAD: `docs/mechanical/requirements.md` and
  `docs/mechanical/cad-adapter.md`
- PCB: `docs/pcb/requirements.md`
- Robotics: `docs/robotics/requirements.md` and
  `docs/robotics/geometry-policy.md`
- Implementation sequencing: `docs/implementation/IMPLEMENTATION_CONTEXT.md`

## Implementation boundaries

- The scaffold generates requirements, plans, configuration guidance, prompts,
  evidence contracts, and handoff artifacts only; it never generates product
  runtime implementation.
- Unresolved decisions remain blocking in the decision ledger. Do not infer
  authority, credentials, production access, fabrication approval, or permission
  for physical effects.

### No runtime generation boundary

Generation may create or update only the approved documentation, planning,
configuration, and harness paths listed in the generated-file manifest. It must
not create application source, executable product behavior, migrations,
deployment payloads, CAD geometry, firmware binaries, or fabrication outputs.
If implementation requires one of those runtime effects, stop at an
implementation-ready handoff and route the work to the authorized downstream
executor.

## Validation expectations

Resolve exact commands from the generated root `AGENTS.md`. Validate the
smallest claim first, retain observable evidence, and finish with the
authoritative local done command. Report unavailable external integrations as
skipped or blocked; never relabel them as passed.
