# Release Checklist

1. Update `CHANGELOG.md`.
2. Stamp metadata:

```bash
python scripts/release_skill_workflow.py stamp-release --tag vX.Y.Z
```

3. Sync the plugin mirror and run the release preflight:

```bash
make sync-mirror
make release-check
```

`make release-check` runs deterministic validation, smoke checks, and the explicit archive smoke test. CI also runs archive smoke on pull requests and again before publishing a release.

4. Create a signed or reviewed Git tag.
5. Publish the GitHub release / plugin artifact.

## Archive build

Build the release archive with:

```bash
make archive
# or
python scripts/build_plugin_archive.py
```

Do not use ad hoc `zip -r` commands for releases; the archive builder applies the canonical include/exclude policy and validates required files.

## Mirror synchronization

The canonical skill source lives at `skills/zero-to-hero/`. The plugin mirror lives at `plugins/zero-to-hero/skills/zero-to-hero/`.

Before release, run:

```bash
make sync-mirror
make release-check
make archive
```

`make archive` refuses to package a release when the plugin mirror differs from the source skill.

## Release integrity sidecars

`make archive` and `scripts/build_plugin_archive.py` write:

```text
dist/zero-to-hero-<version>.zip.sha256
dist/zero-to-hero-<version>.zip.manifest.json
```

Upload these sidecars with the release archive so users can verify artifact integrity and inspect the included-path manifest.

## Release determinism

Release archive generation is tested for deterministic output, matching SHA256 sidecars, and manifest consistency. Run `make release-check` before publishing; use `make archive` or `python scripts/build_plugin_archive.py` to build the final artifact.

- Run `make release-check` and verify deterministic validation, smoke checks, archive checksum sidecar, archive manifest, and per-file manifest hashes.
- The release workflow validates the exact archive that is uploaded to the GitHub release.


## Plugin metadata validation

Release and validation workflows run `python scripts/plugin_metadata_check.py` to verify plugin metadata, marketplace metadata, Codex skill metadata, icon paths, explicit-invocation policy, and version consistency before packaging.


Run `make plugin-metadata` when you only need to validate plugin, marketplace, Codex metadata, icon paths, explicit-invocation policy, and version consistency.


- [ ] Release archive, checksum, and manifest were uploaded together.
- [ ] Release archive contains maintainer scripts/tests/CI definitions needed for post-extraction validation.
