# Generated-file manifest

Every generation phase must maintain a reviewable manifest at:

```txt
.codex/reports/zero-to-hero/generated-files.manifest.yaml
```

Minimum schema:

```yaml
files_created:
  - path: docs/00-meta/source-of-truth-map.yaml
    phase: canonical_docs_pack
    reason: canonical source-of-truth routing
    source_inputs:
      - .omx/context/zero-to-hero-interview.md
files_modified:
  - path: package.json
    phase: harness_pack
    reason: add check scripts
files_not_touched:
  - path: src/
    reason: zero-to-hero does not implement product runtime code
```

The manifest is not a changelog. It is a review surface for what the skill generated and why.
