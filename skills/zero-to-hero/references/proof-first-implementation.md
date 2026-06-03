# Proof-first implementation principle

Zero-to-hero prepares a repo so implementation agents can prove completion rather than merely claim it.

For every generated implementation task or handoff story, require:

- source docs followed;
- files expected to change;
- files forbidden to change;
- acceptance criteria;
- checks to run;
- runtime or design evidence to produce;
- stop conditions;
- user decisions still required.

Completion evidence may include screenshots, traces, local database snapshots, event logs, audit logs, simulator logs, test output, build output, and generated reports. For code-facing repos, prefer one local done command that composes the required checks.

The skill should not generate vague implementation tasks such as “build dashboard” or “wire backend.” It should generate proof-oriented tasks such as “complete farm dashboard upload flow with form validation, local persistence, query invalidation, audit event, reload verification, and Playwright trace.”
