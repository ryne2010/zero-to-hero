# Minimum viable proof by capability

Implementation-ready does not mean production code exists. It means the repo defines what proof later agents must produce.

## Web frontend

Required proof:

- route-to-story map;
- approved design direction or explicit no-design scope;
- action binding contracts for visible controls;
- form lifecycle contracts for critical forms;
- route screenshots/evidence policy;
- no-scaffold/no-dead-control checks.

## API/backend

Required proof:

- API contract or endpoint map;
- authz/error/idempotency contracts;
- integration test plan;
- runtime evidence policy.

## Database

Required proof:

- schema source of truth;
- migration policy;
- seed/scenario policy;
- backup/restore or local reset policy.

## Mechanical/CAD

Required proof:

- dimensions and tolerances;
- material/manufacturing assumptions;
- CAD generation path;
- review checklist;
- fabrication disclaimer.

## PCB/electronics

Required proof:

- block diagram;
- power tree;
- BOM policy;
- ERC/DRC path;
- fabrication output expectations;
- human review requirement.

## Firmware/robotics

Required proof:

- hardware interface map;
- bring-up plan;
- test jig/simulation policy;
- safety stop conditions;
- telemetry/logging expectations.
