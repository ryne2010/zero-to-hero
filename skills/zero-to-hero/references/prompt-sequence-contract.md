# Prompt sequence contract

Prompt identifiers, order, filenames, applicability, and complete phase
contracts are defined once in `contract-graph.yaml`. The Markdown files under
`prompts/` are generated views.

Every prompt contains a goal, required reads, entry criteria, constraints,
allowed and forbidden writes, outputs, evidence/checks, stop conditions,
explicit done criteria, and the no-runtime-implementation boundary.

Run:

```bash
python scripts/sync_contract_views.py .
python scripts/prompt_sequence_check.py .
```

Any missing field, order drift, stale rendered prompt, or runtime-code write
permission is a validation failure.
