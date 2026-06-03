# Skill pack health check

`validate_zero_to_hero_pack.py` should report quality, not just file existence.

Required checks:

```txt
frontmatter valid
canonical prompt sequence present
no duplicate prompt phase numbers
phase state machine present and parseable
output profiles present
fixtures present
fixture tests pass
cleanup allowlist present
minimum viable proof reference present
scripts compile
YAML parse passes
```

The script should print a human-readable health report and exit non-zero when a required quality gate fails.

## Healthy pack checklist

A healthy zero-to-hero pack has:

- one canonical prompt sequence;
- no duplicate prompt files for the same phase;
- phase state machine present;
- output profiles present;
- fixture tests present and passing;
- generated-file manifest policy present;
- decision ledger policy present;
- cleanup allowlist present;
- minimum viable proof defined;
- hardware safety review present;
- SKILL.md frontmatter valid;
- all YAML/JSON parseable;
- references not broken;
- no generated cache files in the distributed ZIP.


## Skill check modes

Use `python scripts/zero_to_hero_check.py .` for the fastest structural check. Use `python scripts/skill_pack_health.py .` for a concise operational health report. Both default paths are bounded and avoid target-repo smoke checks.

Use `--deep` before packaging or distribution to add deterministic fixture, YAML, reference, and instruction-trust self-checks. Use `--target-smoke` only when you explicitly want environment-sensitive fixture/toolchain probes.

Recommended cadence:

```bash
python scripts/zero_to_hero_check.py .
python scripts/skill_pack_health.py .
python scripts/zero_to_hero_check.py . --deep
python scripts/zero_to_hero_check.py . --deep --summary
python scripts/skill_pack_health.py . --deep --timeout 20 --max-seconds 180
```

Optional target-smoke check:

```bash
python scripts/skill_pack_health.py . --deep --target-smoke --timeout 20 --max-seconds 240
```
