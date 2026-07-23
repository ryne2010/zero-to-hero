# Workflow overview

`references/contract-graph.yaml` is the executable source of truth for phase
identifiers, order, applicability, writes, evidence, stop conditions, prompt
views, and completion criteria. Do not maintain a second sequence here.

The workflow moves from approved intent and exact capability evidence through
canonical documentation, applicable design/hardware contracts, a Codex-native
harness, a neutral implementation handoff, lossless cleanup, and readiness
review. Optional OMX state is CLI-owned and never canonical.

Every decision is classified as `explicit`, `inferred`, `unresolved`,
`rejected`, or `out_of_scope`. Inferred and unresolved behavior cannot silently
become product policy.

Verify the executable sequence with:

```bash
python scripts/sync_contract_views.py .
python scripts/prompt_sequence_check.py .
```
