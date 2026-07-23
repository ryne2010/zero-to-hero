# Generated-file manifest

The one canonical manifest is:

```text
docs/00-meta/generated-files.manifest.yaml
```

It is JSON-compatible YAML so the dependency-free runtime can emit and inspect
it, while the release gate validates it against
`schemas/generated-files-manifest.schema.yaml`.

## Transaction contract

The generator first resolves repository evidence, approved capabilities, and
composable output profiles from their executable contracts. It then renders all
selected required artifacts into a staging tree, checks required and forbidden
paths, rejects symlink traversal, verifies substantive content, and validates
the complete manifest before changing the target repository.

The commit uses same-filesystem atomic replacement for each file. Every
pre-existing destination is snapshotted and every newly created destination is
tracked. A commit error restores prior bytes and removes newly created files, so
a failed child check, staged validation, or commit cannot leave an apparently
complete partial scaffold.

Existing target files are preserved by default. Replacement requires one exact
selected path per `--force TARGET_PATH`; there is no global force switch. The
manifest itself is the transaction record and is refreshed on every successful
write.

## Required per-file evidence

Each selected artifact has one record containing:

- `target_path` and its contract-derived `source`
- every selected `profile` and approved or detected `capability`
- `action`: `create`, `modify`, or `skip`
- `pre_write_sha256` and `post_write_sha256`
- an exact `regeneration_command`
- `validation_evidence`, `generated_status`, and `ownership`
- `external_provenance`, including source, version, license, and audit date when
  external material influenced that artifact

A created file has a null pre-write hash. The manifest's own post-write hash is
null because embedding its digest would be recursively self-referential; its
record must carry `manifest-self-reference` status and explicit validation
evidence.

## Review rules

- `status: complete` means staging and validation passed before commit.
- A `skip` record means target-owned content was preserved and validated as the
  required result.
- Paths forbidden by any selected standalone profile remain absent unless
  another profile in the approved composition requires that exact path.
- Product runtime source and OMX-owned runtime state remain listed under
  `files_not_touched`.
- The target audit fails when a required file is missing or non-substantive,
  a forbidden file exists, a child validation fails, or a recorded hash no
  longer matches.
