# zero-to-hero Codex skill

`zero-to-hero` converts a product idea, partial prototype, or messy repository into a clean, canonical, implementation-ready repo for Codex/OMX.

It generates source-of-truth docs, feature/workflow specs, design packs, hardware packs when applicable, product harness layers, repo-scoped skills, `.omx` handoff artifacts, and a final cleanup report. It does not implement product runtime code.

## Install

Copy this directory into the target repo:

```txt
.agents/skills/zero-to-hero/
```

## Recommended invocation

In Codex:

```txt
Use the zero-to-hero skill.
Start with the deep interview and do not implement product runtime code.
```

For an existing repo, first run the guided start command from the skill directory:

```bash
python scripts/zero_to_hero_start.py /path/to/repo --profile auto --write
```

This writes a start report plus the target-repo audit under `.codex/reports/zero-to-hero/`.

To preview generated templates without writing files:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto
```

To apply selected templates after reviewing the dry-run manifest:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto --write --require-clean
```

Use `--profile full` only when the repo truly needs every product surface.

## Canonical workflow

```txt
deep interview
→ research and capability detection
→ canonical docs pack
→ approved design/visual pack
→ hardware/mechanical/PCB pack when applicable
→ frontend parity system
→ product usability contract
→ local product done harness
→ repo-scoped implementation skills
→ OMX single aggregate goal handoff
→ lossless canonical cleanup
→ implementation readiness review
```


## Prompt bundles

To produce a durable prompt bundle for a target repo:

```bash
python scripts/render_prompt_bundle.py . --group all --target-repo /path/to/repo --write
```

## Build a clean ZIP

To distribute the skill without cache or runtime artifacts:

```bash
python scripts/build_skill_zip.py . --out zero-to-hero-codex-skill-pack.zip
```

## Health and release checks

Use the fast checks for day-to-day validation:

```bash
python scripts/zero_to_hero_check.py .
python scripts/zero_to_hero_doctor.py .
```

Use deeper deterministic checks before packaging or distribution:

```bash
python scripts/zero_to_hero_check.py . --deep
python scripts/zero_to_hero_doctor.py . --deep
```

Executable target smoke checks are separate from the main check runner. Run fixture and toolchain probes directly only when needed:

```bash
python scripts/run_fixture_tests.py .
python scripts/toolchain_preflight.py fixtures/react-vite-scaffold
python scripts/external_context_inventory.py fixtures/react-vite-scaffold
python scripts/repo_safety_check.py fixtures/react-vite-scaffold
```

For long interactive runs, add `--jsonl` to `zero_to_hero_check.py` or `--json` to `zero_to_hero_doctor.py` for machine-readable output. See `references/check-operability.md`.

## Distribution hygiene

The distributed skill pack must not include generated cache directories, `.codex` report artifacts, duplicate prompt phases, or stale reference files. Run the deep check path before sharing a ZIP:

```bash
python scripts/zero_to_hero_check.py . --deep
python scripts/build_skill_zip.py . --out zero-to-hero-codex-skill-pack.zip
```

## Small reliability utilities

- `scripts/zero_to_hero_start.py --write` writes a start report, target-repo audit, and template dry-run summary.
- `scripts/target_repo_audit.py --write` writes preflight reports under `.codex/reports/zero-to-hero/`.
- `scripts/apply_zero_to_hero_templates.py --profile auto` applies capability-aware templates.
- `scripts/instruction_trust_scan.py` reports untrusted instruction-like content in target repos.
- `scripts/prompt_sequence_check.py` verifies the canonical prompt sequence is complete and non-overlapping.
- `scripts/render_prompt_bundle.py` emits copy/paste prompt bundles for target repos.
- `scripts/build_skill_zip.py` creates a clean distributable skill ZIP.

## Invocation policy

`zero-to-hero` is intentionally configured for explicit invocation. Use `$zero-to-hero` or explicitly say “Use the zero-to-hero skill” so it does not activate during ordinary coding tasks.
