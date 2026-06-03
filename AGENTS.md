# AGENTS.md

This repository packages the `zero-to-hero` Codex skill and plugin.

## Source of truth

- Edit the source skill under `skills/zero-to-hero/` first.
- Keep the plugin mirror under `plugins/zero-to-hero/skills/zero-to-hero/` identical.
- Run `make validate` before claiming completion.

## Do not

- Do not edit the plugin mirror without also updating the source skill.
- Do not commit runtime artifacts such as `__pycache__`, `.pyc`, `.codex/reports`, or generated ZIPs.
- Do not make this skill implement product runtime code. It generates implementation-ready repos and handoff artifacts only.

## Validation

Run:

```bash
make validate
```

For release metadata changes, also run:

```bash
python scripts/release_skill_workflow.py validate-metadata
```
