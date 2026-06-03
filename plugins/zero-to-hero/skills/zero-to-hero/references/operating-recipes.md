# Operating recipes

Use these recipes to choose the smallest effective zero-to-hero path for a target repo. The skill remains planning, specification, harness, and handoff focused; it does not implement product runtime code.

## Idea-only product

1. Run the deep interview.
2. Run research and capability detection.
3. Generate the canonical docs pack.
4. Generate design, hardware, or PCB packs only when the interview makes those capabilities relevant.
5. Generate the harness pack and OMX handoff.
6. Run canonical cleanup and implementation-readiness review.

## Existing messy repo

1. Run `scripts/zero_to_hero_start.py /path/to/repo --profile auto --write`.
2. Review `.codex/reports/zero-to-hero/start-here.md` and `target-repo-audit.md`.
3. Run the target-repo preflight prompt.
4. Apply templates only after reviewing the dry-run manifest.
5. Run canonical cleanup after generation.

## Frontend looks close but is not usable

1. Generate or repair the Frontend Parity System.
2. Generate or repair the Product Usability Contract.
3. Generate or repair the Local Product Done Harness.
4. Use `$ralplan` to produce a current-state gap analysis and task graph.
5. Execute only an approved task graph through `$ultragoal`.
6. Use `$ralph` for final visual, workflow, and evidence review.

## API/backend service

1. Skip visual target generation unless the repo also has a UI.
2. Focus on contracts, authz, dataflow, negative paths, runtime evidence, local simulators, observability, and local product done gates.
3. Require contract tests, role/permission walkthroughs, and traceability from endpoint to test/evidence.

## Hardware, mechanical, PCB, firmware, or robotics product

1. Run source research before treating parts, standards, manufacturing, or safety assumptions as canonical.
2. Generate requirements, constraints, interfaces, safety limits, test plans, and manufacturing handoff docs before generation artifacts.
3. Keep CAD/PCB/firmware outputs review-gated.
4. Do not treat generated CAD, PCB, or firmware as manufacturing-approved without human engineering review.

## Small low-risk product

Use the one-shot prompt only when scope is small, low-risk, and non-regulated. If ambiguity appears, stop and return to the stepwise workflow.
