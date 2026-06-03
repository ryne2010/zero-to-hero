# Target repo audit report

`target_repo_audit.py` inventories a target repository before zero-to-hero generation. It detects capabilities, existing source-of-truth artifacts, OMX structure, repo-scoped skills, and instruction-trust risk.

Use `--write` to create:

```txt
.codex/reports/zero-to-hero/target-repo-audit.json
.codex/reports/zero-to-hero/target-repo-audit.md
```

The report is evidence for the first planning phase. It should not be treated as product implementation.
