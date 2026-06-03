# zero-to-hero quickstart

1. Copy `.agents/skills/zero-to-hero/` into the target repository.
2. For an existing repo, run preflight from the skill directory:

```bash
python scripts/repo_safety_check.py /path/to/repo --write
python scripts/target_repo_audit.py /path/to/repo --write
python scripts/toolchain_preflight.py /path/to/repo --write
python scripts/external_context_inventory.py /path/to/repo --write
```

3. Preview capability-aware templates before writing:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto
```

4. Apply templates only after review:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto --write --require-clean
```

5. Optionally render a prompt bundle:

```bash
python scripts/render_prompt_bundle.py . --group canonical --target-repo /path/to/repo --write
```

6. In Codex, invoke:

```txt
Use the zero-to-hero skill. Start with the deep interview. Do not implement product runtime code.
```

7. Follow the canonical prompt sequence under `prompts/`.
8. Finish with canonical cleanup and implementation-readiness review.

For skill-pack maintenance, run the fast checks during normal use:

```bash
python scripts/zero_to_hero_check.py .
python scripts/zero_to_hero_doctor.py .
python scripts/prompt_sequence_check.py .
python scripts/instruction_trust_scan.py fixtures/prompt-injection-risk
```

Before packaging or distribution, run deeper deterministic checks and build a clean ZIP:

```bash
python scripts/zero_to_hero_check.py . --deep
python scripts/zero_to_hero_doctor.py . --deep
python scripts/build_skill_zip.py . --out zero-to-hero-codex-skill-pack.zip
```

## Invocation policy

`zero-to-hero` is intentionally configured for explicit invocation. Use `$zero-to-hero` or explicitly say “Use the zero-to-hero skill” so it does not activate during ordinary coding tasks.

## Existing repo quick start

```bash
python scripts/zero_to_hero_start.py /path/to/repo --profile auto --write
```

Review `.codex/reports/zero-to-hero/start-here.md` before applying templates or generating docs.
