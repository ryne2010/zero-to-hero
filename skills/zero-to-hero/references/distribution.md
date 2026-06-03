# Distribution

Use `scripts/build_skill_zip.py` to package this skill for distribution.

The package builder:

- runs `scripts/zero_to_hero_check.py` unless `--skip-check` is provided;
- excludes `__pycache__`, `.pyc`, `.git`, and other runtime cache artifacts;
- preserves the repo-scoped skill path `.agents/skills/zero-to-hero/` inside the ZIP.

Example:

```bash
python scripts/build_skill_zip.py . --out zero-to-hero-codex-skill-pack.zip
```

Do not manually zip a working tree that contains runtime reports, cache directories, or target-repo artifacts.
