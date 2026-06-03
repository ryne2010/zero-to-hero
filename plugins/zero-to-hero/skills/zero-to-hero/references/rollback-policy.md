# Generated artifact rollback policy

`zero-to-hero` modifies target repos directly only in explicit generation modes. Every run must be reviewable and reversible.

Required outputs:

```txt
.codex/reports/zero-to-hero/generated-files.manifest.yaml
.codex/reports/zero-to-hero/change-summary.md
.codex/reports/zero-to-hero/unresolved-decisions.md
```

Rollback guidance:

1. Never overwrite a non-generated file without listing it in the manifest.
2. Prefer additive docs/templates/scripts unless canonical cleanup is explicitly requested.
3. Preserve moved/merged content in the cleanup report.
4. If cleanup merges duplicate docs, record the source paths and the target canonical path.
5. Do not remove app source files.
6. Do not remove user-authored product decisions; normalize their location instead.
