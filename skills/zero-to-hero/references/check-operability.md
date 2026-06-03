# Check operability

`zero-to-hero` keeps routine validation side-effect-free. The default checks do not spawn nested target-repo toolchain probes, which makes them reliable inside Codex/OMX sandboxes and CI wrappers.

## Fast structural check

```bash
python scripts/zero_to_hero_check.py .
```

Use this after ordinary edits. It validates required files, prompt sequence, metadata, and packaged runtime cleanliness.

## Deep structural check

```bash
python scripts/zero_to_hero_check.py . --deep
python scripts/zero_to_hero_check.py . --deep --summary
```

Use this before packaging or distribution. It adds deep file presence checks, YAML parsing, reference smoke checks, and output-profile coverage. It remains side-effect-free.

## Target and fixture smoke checks

Executable smoke checks are intentionally separate. Run them directly when you want to exercise fixture repos or local toolchain probes:

```bash
python scripts/run_fixture_tests.py .
python scripts/toolchain_preflight.py fixtures/react-vite-scaffold
python scripts/external_context_inventory.py fixtures/react-vite-scaffold
python scripts/repo_safety_check.py fixtures/react-vite-scaffold
```

`zero_to_hero_check.py --target-smoke` reports this guidance but does not execute those probes. This avoids nested-subprocess flakiness in constrained agent environments.

## Doctor

```bash
python scripts/zero_to_hero_doctor.py .
python scripts/zero_to_hero_doctor.py . --deep
python scripts/zero_to_hero_doctor.py . --json
```

The doctor is a human-friendly structural diagnostic. It is also side-effect-free. Use the check runner for machine-oriented gates and the doctor for quick operational diagnosis.

## JSONL

```bash
python scripts/zero_to_hero_check.py . --deep
python scripts/zero_to_hero_check.py . --deep --summary --jsonl
```

`--jsonl` streams internal structural check events and a final summary.

## Health check

```bash
python scripts/skill_pack_health.py .
python scripts/skill_pack_health.py . --deep --timeout 20 --max-seconds 180
python scripts/skill_pack_health.py . --deep --target-smoke --timeout 20 --max-seconds 240
```

The health check is an operational summary. Deep mode runs deterministic self-checks; `--target-smoke` must be explicit for environment-sensitive probes.

