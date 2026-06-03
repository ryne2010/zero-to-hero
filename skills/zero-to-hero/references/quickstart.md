# Quickstart

Install this skill under the target repository:

```txt
.agents/skills/zero-to-hero/
```

Start with:

```txt
Use the zero-to-hero skill.
Start with the deep interview. Do not implement runtime product code.
```

Use the stepwise sequence for serious products. Use the one-shot prompt only for small, low-risk products where inferred decisions are acceptable.


## Skill check modes

Use `python scripts/zero_to_hero_check.py .` for a fast structural check. Use `python scripts/zero_to_hero_check.py . --deep` before packaging or distribution to run slower fixture and toolchain smoke checks.
