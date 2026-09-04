# zero-to-hero quickstart

1. Install the skill at `.agents/skills/zero-to-hero/`.
2. Inspect an existing repository without writing:

```bash
python scripts/target_repo_audit.py /path/to/repo --preflight
```

3. Preview automatically selected artifacts:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto
```

An empty repository requires approved capability evidence or explicit profiles;
it does not silently become docs-first.

4. For approved composite scope, repeat profiles:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --profile mobile-app --profile api-service
```

5. Review the preview and write only from a clean, safe Git branch:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --profile mobile-app --profile api-service --write
```

Existing targets are preserved. Use `--force <exact-generated-path>` only for a
reviewed, scoped replacement.

6. Specialize generated documentation outside the machine-owned command
markers, then refresh the command inventory and manifest hashes:

```bash
python3 scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --write --refresh-manifest
```

7. After committing an unchanged handoff, reproduce it only with the
force-free `--write --replay-manifest` command recorded in the manifest. Run
that command from the target repository root. Changed approval evidence
requires a new explicit clean selection transaction.

8. Run the post-generation audit:

```bash
python scripts/target_repo_audit.py /path/to/repo \
  --profile mobile-app --profile api-service
```

9. Continue with the lifecycle and prompt order generated from
`references/contract-graph.yaml`. The implementation handoff remains neutral
unless an operational optional adapter is explicitly selected.

The skill is explicitly invoked and never implements product runtime code.
