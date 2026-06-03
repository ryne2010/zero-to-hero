# Contributing

Thank you for improving `zero-to-hero`. This repository packages a Codex skill and plugin that prepares product ideas or in-progress repos for implementation. It does not implement target product runtime code.

## Development principles

- Keep the skill focused on interview, research, source-of-truth generation, harness generation, handoff artifacts, and lossless cleanup.
- Do not add target-product runtime implementation behavior to the skill.
- Prefer small, testable improvements over broad workflow expansion.
- Preserve the source skill and plugin mirror byte-for-byte.
- Keep generated/runtime artifacts out of commits and release archives.

## Repository layout

- `skills/zero-to-hero/` is the source skill of truth.
- `plugins/zero-to-hero/skills/zero-to-hero/` is the plugin mirror.
- `plugins/zero-to-hero/.codex-plugin/plugin.json` contains plugin metadata.
- `.agents/plugins/marketplace.json` is a local marketplace example.

## Edit workflow

1. Make source edits under `skills/zero-to-hero/`.
2. Sync the plugin mirror:

```bash
make sync-mirror
```

3. Validate the repo:

```bash
make validate
```

4. Build the deterministic release archive when needed:

```bash
make archive
```

## Pull request checklist

Before opening a pull request, confirm:

- [ ] Source skill and plugin mirror are synchronized.
- [ ] `make validate` passes.
- [ ] `make archive` passes when release packaging is touched.
- [ ] No `__pycache__`, `.pyc`, `.pyo`, `dist/`, or generated `.codex` report artifacts are committed.
- [ ] No target-product runtime implementation behavior was added.
- [ ] New prompts or references are linked from the relevant manifest or documentation.
- [ ] New scripts have bounded/default-safe behavior.
- [ ] Security-sensitive reports avoid echoing untrusted instructions by default.

## Release workflow

Use the release checklist in `docs/RELEASE_CHECKLIST.md`. Releases should use the deterministic archive builder, not ad hoc zip commands.
