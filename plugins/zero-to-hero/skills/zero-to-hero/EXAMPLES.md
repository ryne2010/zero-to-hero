# zero-to-hero examples

These examples show how to use the skill without changing product runtime code.

## Idea-only product

```txt
Use the zero-to-hero skill.
Start with the deep interview for this product idea. Do not generate files until I approve the interview summary.
```

After approval, continue through the canonical prompt sequence and generate a source-of-truth repo foundation.

## Existing web app repo

From the skill directory:

```bash
python scripts/target_repo_audit.py /path/to/repo --write
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto
python scripts/render_prompt_bundle.py . --group canonical --target-repo /path/to/repo --write
```

Review the dry-run manifest before applying templates with `--write`.

## Hardware / PCB repo

```bash
python scripts/target_repo_audit.py /path/to/hardware-repo --write
python scripts/apply_zero_to_hero_templates.py /path/to/hardware-repo --profile auto
```

The `auto` profile should select hardware/PCB/firmware packs when KiCad, CAD, firmware, or robotics markers are detected. Human engineering review is still required before fabrication or safety-critical use.

## Prompt bundle generation

To create a copy/paste prompt bundle:

```bash
python scripts/render_prompt_bundle.py . --group all --target-repo /path/to/repo --write
```

The bundle is written under:

```txt
.codex/reports/zero-to-hero/prompt-bundle.md
```

## Clean distribution ZIP

To package the skill itself:

```bash
python scripts/build_skill_zip.py . --out zero-to-hero-codex-skill-pack.zip
```
