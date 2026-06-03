# Maintaining zero-to-hero

This guide summarizes the maintenance workflow for the plugin repository.

## Source and mirror

The canonical skill source is:

```text
skills/zero-to-hero/
```

The plugin mirror is:

```text
plugins/zero-to-hero/skills/zero-to-hero/
```

After changing the source skill, run:

```bash
make sync-mirror
make validate
```

The release archive builder refuses to package an out-of-sync mirror.

## Validation levels

Use the repo-level validation target for normal maintenance:

```bash
make validate
```

`make validate` is deterministic and structural. Use focused targets when you want a narrower signal:

```bash
make help          # discover available maintainer commands
make doctor        # fast operational doctor for the source skill
make deep-doctor   # deterministic deep doctor for release confidence
make mirror-parity # verify source and plugin mirror parity
make smoke         # bounded runtime smoke checks
make archive-smoke # explicit deterministic archive/checksum/manifest gate
make release-check # validate + smoke + archive smoke
```

Use individual skill checks when working inside the skill:

```bash
python skills/zero-to-hero/scripts/zero_to_hero_check.py skills/zero-to-hero
python skills/zero-to-hero/scripts/zero_to_hero_check.py skills/zero-to-hero --deep --max-seconds 240 --summary
```

## Release artifacts

Release archives are deterministic and include sidecars:

```text
dist/zero-to-hero-<version>.zip
dist/zero-to-hero-<version>.zip.sha256
dist/zero-to-hero-<version>.zip.manifest.json
```

The `.sha256` file supports integrity verification. The manifest records the archive hash, file count, deterministic timestamp, and included paths.

## Governance files

- `CONTRIBUTING.md` defines contribution expectations.
- `SECURITY.md` defines private security reporting and skill safety boundaries.
- `.github/PULL_REQUEST_TEMPLATE.md` defines PR evidence expectations.
- `.github/dependabot.yml` keeps GitHub Actions versions current.

## What not to add

Avoid adding target-product runtime implementation behavior to this repository. `zero-to-hero` prepares implementation-ready repos; it does not build user products itself.

## CI archive smoke

The validate workflow runs `make validate`, `make smoke`, and then `make archive-smoke` as separate explicit gates. This catches packaging drift on pull requests instead of waiting until a manual release. The release workflow also runs the archive smoke test after building the release archive and before creating the GitHub release.


## Plugin metadata validation

Release and validation workflows run `python scripts/plugin_metadata_check.py` to verify plugin metadata, marketplace metadata, Codex skill metadata, icon paths, explicit-invocation policy, and version consistency before packaging.


Run `make plugin-metadata` when you only need to validate plugin, marketplace, Codex metadata, icon paths, explicit-invocation policy, and version consistency.
