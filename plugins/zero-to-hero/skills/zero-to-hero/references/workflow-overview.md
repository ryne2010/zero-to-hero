# zero-to-hero workflow overview

The skill moves from ambiguous idea to implementation-ready repository through a controlled set of phases. The output is a repository that later implementation agents can build from with minimal ambiguity.

## Operating principle

Do not let an idea, visual, sketch, CAD prompt, or generated artifact become product policy automatically. Every inferred behavior must be classified as:

```txt
explicit     stated or approved by the user
inferred     derived by the agent and awaiting review
unresolved   cannot be safely decided without user input
rejected     explicitly not part of the canonical design
out_of_scope intentionally outside the repo's implementation target
```

## Execution summary

```txt
1. interview: discover product intent, users, constraints, non-goals, risks.
2. research: verify external facts and detect capabilities.
3. docs pack: create canonical product/architecture/story/workflow docs.
4. design pack: create and approve visual/mechanical/art direction targets, then deconstruct them into contracts.
5. hardware pack: add mechanical/CAD/PCB/firmware packs when the product needs them.
6. harness pack: add frontend parity, product usability, runtime evidence, traceability, local simulator, and local done gates.
7. repo skills: add only the repo-scoped skills needed for implementation workflows.
8. OMX pack: create one aggregate goal with ordered stories.
9. cleanup: remove iteration residue and reconcile duplicate sources without losing substance.
10. readiness: produce final handoff and proof that the repo is implementation-ready.
```
