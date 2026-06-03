# Template application profiles

`zero-to-hero` templates are profile-aware. The default application mode is `auto`, which detects target-repo capabilities and applies only relevant docs, skills, and handoff scaffolding.

This prevents a web app from receiving PCB/mechanical docs by default, or an API-only repo from receiving frontend parity files unless the repo actually has a UI capability.

## Command

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto
```

The script is dry-run by default. Add `--write` only after reviewing the generated-file manifest.

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto --write
```

## Profiles

- `auto`: detect capabilities and select profiles automatically.
- `base`: source-of-truth, Codex/OMX, reports, artifacts, and implementation-context templates only.
- `full`: apply every template.
- `web-app`: UI/frontend parity, product-execution, and local-mode skills.
- `mobile-app`: mobile/frontend parity, product-execution, and local-mode skills.
- `desktop-app`: desktop/frontend parity, product-execution, and local-mode skills.
- `api-service`: product-execution and local-mode skills without UI docs.
- `cli-tool`: product-execution and local-mode skills without UI docs.
- `ai-agent-app`: product-execution and local-mode skills.
- `data-ml-app`: product-execution and local-mode skills.
- `infra-repo`: product-execution and local-mode verification docs.
- `firmware-iot`: hardware, firmware, product-execution, and local-mode verification docs.
- `mechanical-product`: hardware, mechanical, product-execution, and local-mode verification docs.
- `pcb-electronics`: hardware, PCB, product-execution, and local-mode verification docs.
- `robotics-product`: hardware, firmware, mechanical, PCB, product-execution, and local-mode verification docs.
- `docs-first-product`: docs/product-execution and local-mode verification docs.

## Manifest semantics

The generated manifest includes:

- requested profile;
- selected profiles;
- capability detection evidence;
- files that would be created;
- files that would be overwritten if `--force` were used;
- files skipped because they already exist;
- files skipped because they are not selected by the active profile.

## Safety rules

- Do not use `--force` unless the user explicitly approves overwriting existing repo files.
- Use `--profile full` only when the target repo truly needs all product surfaces.
- Hardware profiles create engineering-intent docs only; they do not approve fabrication.
- The apply script never writes product runtime implementation code.
