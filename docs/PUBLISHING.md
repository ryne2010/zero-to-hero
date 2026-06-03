# Publishing

This repo is structured for both skill and plugin distribution.

- `skills/zero-to-hero/` is the source skill.
- `plugins/zero-to-hero/` is the installable plugin wrapper.
- `.agents/plugins/marketplace.json` is a local marketplace example.

CI validates metadata, source/mirror parity, and skill health before publishing.

## Release archive policy

Publishing should use:

```bash
python scripts/build_plugin_archive.py
```

The builder excludes runtime/generated artifacts and validates the plugin metadata, source skill, plugin mirror, marketplace entry, and root handoff files.


## Publishing guardrails

Run these before publishing:

```bash
make sync-mirror
make validate
make archive
```

The deterministic archive builder checks required files, excludes runtime artifacts, and refuses to package if the source skill and plugin mirror are out of sync.

## Release integrity sidecars

`make archive` and `scripts/build_plugin_archive.py` write:

```text
dist/zero-to-hero-<version>.zip.sha256
dist/zero-to-hero-<version>.zip.manifest.json
```

Upload these sidecars with the release archive so users can verify artifact integrity and inspect the included-path manifest.


## Release determinism

Release archive generation is tested for deterministic output, matching SHA256 sidecars, and manifest consistency. Run `make release-check` before publishing; use `make archive` or `python scripts/build_plugin_archive.py` to build the final artifact.

The release workflow validates the exact generated archive before upload, including checksum, manifest, and per-file archive-entry hashes.


## Plugin metadata validation

Release and validation workflows run `python scripts/plugin_metadata_check.py` to verify plugin metadata, marketplace metadata, Codex skill metadata, icon paths, explicit-invocation policy, and version consistency before packaging.


Run `make plugin-metadata` when you only need to validate plugin, marketplace, Codex metadata, icon paths, explicit-invocation policy, and version consistency.


Publish the generated archive, checksum, and manifest together. The archive is intentionally source-complete for validation: it includes the plugin/skill payload plus maintainer scripts, tests, and CI workflow definitions.
