# Target repo audit report

`target_repo_audit.py` consumes the executable graph and selected profile
composition. Preflight mode inventories capability, commands, source authority,
repository safety, and instruction-trust risk. Post-generation mode additionally
requires the canonical manifest, substantive required artifacts, absent
forbidden artifacts, and matching hashes.

Use `--write` to create:

```txt
.codex/reports/zero-to-hero/target-repo-audit.json
.codex/reports/zero-to-hero/target-repo-audit.md
```

Child timeout, nonzero exit, invalid JSON, unsupported requested tooling, unsafe
state, and unresolved trust findings fail closed. The report is planning and
readiness evidence, not product implementation.
