# Final stability notes

`zero-to-hero` should stop evolving once the skill passes its own checks and no concrete failure mode is observed in target repos. Add new behavior only when a real repo exposes a repeatable gap that cannot be addressed by existing phases, capability profiles, prompts, or validation scripts.

Do not add product implementation behavior to this skill. Runtime product code belongs in the target repo implementation phase driven by the generated handoff artifacts.


## Check separation

Fixture checks are deterministic by default. Toolchain and target-repo smoke checks are explicit so everyday validation stays bounded and reproducible.


## Doctor quick mode

The check runner and doctor now run side-effect-free structural checks by default. Fixture and toolchain probes are direct, explicit scripts so routine skill maintenance does not depend on environment-sensitive smoke checks.


## Side-effect-free doctor

The doctor script is intentionally structural and non-executing. Use it for quick operational diagnostics. Use `zero_to_hero_check.py --deep` for deterministic structural validation; add `--summary` when concise CI output is preferred. Run fixture/toolchain smoke scripts directly when environment-sensitive evidence is needed.


## Health check target smoke

`skill_pack_health.py` keeps environment-sensitive probes behind `--target-smoke`, matching the main check runner. Routine validation should stay bounded and deterministic; target smoke checks are useful before distribution or when diagnosing a target-repo setup issue.
