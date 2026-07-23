# zero-to-hero prompts

`references/contract-graph.yaml` is the executable source of truth for prompt
order and content. These files are generated views; run
`scripts/sync_contract_views.py` to verify them.

## Standard sequence

1. `00-deep-interview.md`
2. `01-research-and-capability-detection.md`
3. `02-canonical-docs-pack.md`
4. `03-design-visual-pack.md`
5. `04-hardware-mechanical-pcb-pack.md` when applicable
6. `05-frontend-parity-system.md` when UI exists
7. `06-product-usability-contract.md` when app workflows exist
8. `07-local-product-done-harness.md`
9. `08-implementation-handoff.md`
10. `09-canonical-cleanup.md`
11. `10-implementation-readiness-review.md`

## Optional prompts

- `98-target-repo-preflight.md` inspects an existing repo before the interview.
- `99-one-shot-small-product.md` is only for low-risk, small products.
