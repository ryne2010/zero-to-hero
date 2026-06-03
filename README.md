# zero-to-hero

`zero-to-hero` is an installable Codex plugin and skill pack that turns product ideas, prototypes, or messy repositories into clean, canonical, implementation-ready repositories for Codex/OMX.

It generates source-of-truth docs, user stories, workflows, design/UI/hardware specs, frontend parity contracts, product usability harnesses, local-product validation gates, repo-scoped skills, OMX handoff artifacts, and lossless cleanup. It does **not** implement product runtime code.

## Distribution surfaces

- Source skill: `skills/zero-to-hero/`
- Plugin mirror: `plugins/zero-to-hero/skills/zero-to-hero/`
- Plugin metadata: `plugins/zero-to-hero/.codex-plugin/plugin.json`
- Local marketplace example: `.agents/plugins/marketplace.json`

The source skill and plugin mirror are expected to be byte-for-byte identical. CI enforces this with `tests/check_skill_mirror.py`, and release archive generation refuses to package an out-of-sync mirror.

After editing `skills/zero-to-hero/`, sync the plugin mirror with:

```bash
make sync-mirror
make validate
```


## Install as a project skill

```bash
gh skill install ./skills/zero-to-hero --agent codex --scope project
```

Or copy the skill into a target repository:

```bash
mkdir -p .agents/skills
cp -R skills/zero-to-hero /path/to/target-repo/.agents/skills/zero-to-hero
```

## Use as a plugin

The plugin wrapper lives at:

```text
plugins/zero-to-hero/
```

A local marketplace entry is included at:

```text
.agents/plugins/marketplace.json
```

## Validate

```bash
make validate
```

Validation is split into deterministic structural checks and explicit smoke checks. `make validate` runs fast structural validation only. Use `make smoke` for runtime smoke checks, `make archive-smoke` for release archive validation, and `make release-check` for the full pre-release gate.

For day-to-day maintenance, use the narrower command that matches the question you are asking:

```bash
make help          # list maintainer commands
make doctor        # fast operational doctor
make deep-doctor   # deterministic deep doctor
make mirror-parity # verify source skill and plugin mirror match
make smoke         # bounded runtime smoke checks
make archive-smoke # explicit packaging determinism/checksum/manifest gate
make release-check # validate + smoke + archive-smoke before release
```


## Contribution and security

For repository maintenance, see `CONTRIBUTING.md`, `SECURITY.md`, and `docs/MAINTAINING.md`.

## Release

This repo uses semantic versions. The current package version is `0.1.0`.

Release metadata is stored in:

```text
skills/zero-to-hero/release.json
plugins/zero-to-hero/skills/zero-to-hero/release.json
plugins/zero-to-hero/.codex-plugin/plugin.json
pyproject.toml
```

Use:

```bash
python scripts/release_skill_workflow.py stamp-release --tag v0.1.0
make release-check
```

`make release-check` runs deterministic validation, smoke checks, and archive smoke validation. See `docs/RELEASE_CHECKLIST.md` and `docs/PLUGIN_DISTRIBUTION.md`.

## Build release archive

Use the deterministic plugin archive builder instead of ad hoc zip commands:

```bash
make archive
# or
python scripts/build_plugin_archive.py
```

The archive builder uses curated include paths, excludes runtime/generated artifacts, validates required plugin/skill and maintainer files, and writes checksum sidecars plus an archive manifest. Release archives include the skill/plugin plus maintainer scripts, tests, and CI definitions so the artifact remains self-validating after extraction.


## Release determinism

Release archive generation is tested for deterministic output, matching SHA256 sidecars, and manifest consistency. Run `make release-check` before publishing; use `make archive` or `python scripts/build_plugin_archive.py` to build the final artifact.

## CI release packaging guard

Pull-request validation runs deterministic validation, runtime smoke checks, and deterministic archive smoke tests. The release workflow also smoke-tests archive generation before publishing so checksum and manifest sidecars are verified in CI before a release is created.

Release archive generation validates deterministic output, SHA256 sidecars, archive manifests, and per-file manifest hashes. The release workflow smoke-tests the exact archive that will be published.


## Plugin metadata validation

Release and validation workflows run `python scripts/plugin_metadata_check.py` to verify plugin metadata, marketplace metadata, Codex skill metadata, icon paths, explicit-invocation policy, and version consistency before packaging.


Run `make plugin-metadata` when you only need to validate plugin, marketplace, Codex metadata, icon paths, explicit-invocation policy, and version consistency.
