# Prompt bundle

`zero-to-hero` includes `scripts/render_prompt_bundle.py` to turn the canonical prompt sequence into a single copy/paste-friendly Markdown file.

Use it when:

- a user wants to run the sequence in a fresh Codex/OMX thread;
- the repo already has the skill installed but the operator wants a durable prompt transcript;
- a planning review should happen before execution.

Examples:

```bash
python scripts/render_prompt_bundle.py . --group canonical
python scripts/render_prompt_bundle.py . --group all --target-repo /path/to/repo --write
python scripts/render_prompt_bundle.py . --group harness --out /tmp/zero-to-hero-harness-prompts.md
```

Valid groups:

```txt
preflight
canonical
design
harness
handoff
one-shot
all
```

Prompt bundles are generated artifacts. They should not replace the canonical prompt files under `prompts/`.
