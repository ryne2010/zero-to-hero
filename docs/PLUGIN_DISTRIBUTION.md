# Plugin Distribution

The plugin wrapper lives at:

```text
plugins/zero-to-hero/
```

Metadata lives at:

```text
plugins/zero-to-hero/.codex-plugin/plugin.json
```

The plugin points to packaged skills at:

```text
plugins/zero-to-hero/skills/
```

For local testing, `.agents/plugins/marketplace.json` contains a local plugin source. For published distribution, switch the source to a Git-backed plugin path and pinned tag.

## Canonical archive builder

Use `scripts/build_plugin_archive.py` for distributable ZIPs. It is the canonical packaging path for this repo and is exercised by CI smoke tests.


## Mirror parity

The distributed plugin contains a mirror of the source skill under `plugins/zero-to-hero/skills/zero-to-hero/`. Keep the mirror synchronized with:

```bash
make sync-mirror
```

CI and the release archive builder validate mirror parity before packaging.

## Release integrity sidecars

`make archive` and `scripts/build_plugin_archive.py` write:

```text
dist/zero-to-hero-<version>.zip.sha256
dist/zero-to-hero-<version>.zip.manifest.json
```

Upload these sidecars with the release archive so users can verify artifact integrity and inspect the included-path manifest.


## Release determinism

Release archive generation is tested for deterministic output, matching SHA256 sidecars, and manifest consistency. Run `make release-check` before publishing; it runs validate + smoke + archive-smoke. Use `make archive` or `python scripts/build_plugin_archive.py` to build the final artifact.

## Archive smoke gate

The deterministic archive path is validated in CI with `make archive-smoke`. Release artifacts should only be published after the archive ZIP, SHA256 sidecar, and manifest sidecar pass this gate.

Release archives include a `.sha256` sidecar and a `.manifest.json` sidecar with included paths and per-file hashes. Consumers and CI can validate the published artifact without rebuilding it.


## Plugin metadata validation

Release and validation workflows run `python scripts/plugin_metadata_check.py` to verify plugin metadata, marketplace metadata, Codex skill metadata, icon paths, explicit-invocation policy, and version consistency before packaging.


Run `make plugin-metadata` when you only need to validate plugin, marketplace, Codex metadata, icon paths, explicit-invocation policy, and version consistency.


The release archive is deterministic and includes checksum and manifest sidecars. It also includes maintainer scripts, smoke tests, and CI workflow definitions so an extracted archive can still be validated without referring back to the source repository.
