# Capability adapter catalog

`zero-to-hero` must support broad product repos through capability detection, not stack-specific prompt injection.

## Capabilities

| Capability | Detection hints | Harness focus |
|---|---|---|
| web_frontend | package.json frontend deps, src/routes, app/, pages/, components/ | frontend parity, product usability, visual evidence |
| server_rendered_ui | Rails/Django/Laravel templates/routes | route capsules, forms, accessibility, e2e tests |
| mobile_app | React Native, Flutter, Swift/Kotlin mobile dirs | mobile routes, gestures, device screenshots, offline/error states |
| api_backend | OpenAPI, controllers, routes, handlers | API contracts, authz, idempotency, error semantics |
| database | migrations, schemas, ORMs | migrations, seed scenarios, transaction/evidence checks |
| ai_agent_system | prompts, tools, agents, evals | tool permissions, grounding, prompt-injection, evals |
| cli_tool | CLI entrypoints, command parser | command contracts, help text, golden command tests |
| data_ml | notebooks, pipelines, model configs | data lineage, evals, reproducibility, drift checks |
| firmware_iot | firmware dirs, platformio, zephyr, arduino | hardware map, test fixtures, simulators, bring-up plan |
| robotics | ROS/URDF/robot files | state machines, simulation, safety, kinematics/source assets |
| mechanical_cad | CAD assets, product dimensions, enclosure specs | text-to-CAD prompts, STEP/BOM, tolerances, validation |
| pcb_electronics | KiCad, schematics, BOMs, firmware pins | power tree, connector map, DRC/ERC/DFM, test-jig plan |
| infra | Terraform, Docker, CI, Kubernetes | local/production mode, secrets, observability, deploy gates |
| docs_only | docs but little code | source-of-truth structure, task graph, starter repo plan |

## Adapter rule

Capability adapters may change file paths, command suggestions, evidence mechanisms, and generated examples. They must not change product policy or safety invariants.
