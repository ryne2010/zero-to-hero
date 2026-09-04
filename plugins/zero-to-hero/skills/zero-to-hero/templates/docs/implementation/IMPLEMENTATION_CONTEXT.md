# Implementation context

Read in order:

1. `AGENTS.md`
2. `docs/00-meta/source-of-truth-map.yaml`
3. `docs/implementation/IMPLEMENTATION_BRIEF.md`
4. `PLANS.md` for the durable planning contract
5. `docs/implementation/EXECPLAN.md` for the living target-specific plan
6. `docs/implementation/PLANNING_EVIDENCE.md`
7. the profile-specific requirements selected by `docs/AGENT_CONTEXT.md`

The implementation brief is execution-neutral. OMX runtime artifacts are
optional, CLI-owned derivatives rather than source of truth.

Do not expand product scope during implementation. Record a newly discovered
requirement or invariant in the decision ledger and return it to the plan's
consensus gate.
