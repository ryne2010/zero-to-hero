# Executable output profiles

Every profile is defined under `output-profiles/` and validated by
`../schemas/output-profile.schema.json`. Those YAML files—not a Python table or
this document—define detection evidence, approved capability mapping,
composition/defaults, required/optional/forbidden artifacts, and evidence.

List the current vocabulary:

```bash
python scripts/apply_zero_to_hero_templates.py --list-profiles
```

Preview automatic selection:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto
```

Compose approved profiles:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --profile web-app --profile api-service
```

Approved discovery data can select a family in an empty repository:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --approved-capabilities-file /path/to/approved-capabilities.json
```

The generator is dry-run by default, preserves existing files, accepts only
exact scoped `--force` paths, validates a staged tree, and publishes one
canonical YAML manifest after a successful transaction. A generic CMake file is
not firmware evidence, and robotics expands only the defaults declared by its
profile.
