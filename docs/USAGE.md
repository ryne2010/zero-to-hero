# Usage

After installing the skill into a target repo, invoke it explicitly:

```text
Use the zero-to-hero skill. Start with the deep interview. Do not implement product runtime code.
```

For existing repos, run a guided start from the skill directory:

```bash
python .agents/skills/zero-to-hero/scripts/zero_to_hero_start.py . --profile auto
```

The skill should generate docs, harness layers, repo-scoped skills, and OMX handoff artifacts. Product runtime implementation should be delegated to follow-up Codex/OMX execution.
