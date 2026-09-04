# Structured handoff quality rubric

This is an external, model-assisted grader. It complements deterministic trace, path,
ordering, and forbidden-write checks; it never replaces them.

Score each criterion from 0 to 4 and cite concrete repository evidence:

A criterion passes at 3 or 4. Compute the reported total by multiplying each
criterion's weight by `score / 4`, summing the results, and rounding to the nearest
integer, with half-point totals rounded up.

| ID | Weight | Passing standard |
| --- | ---: | --- |
| `target_specificity` | 15 | The handoff reflects the actual repository, approved capability data, and selected profiles rather than generic advice. |
| `commands_and_harness` | 20 | Apply exactly one of the two passing branches below. No nonexistent command may be claimed, and the generated handoff validator never counts as product-behavior evidence. |
| `phase_and_ownership` | 15 | Phase order, consensus, leader-only state ownership, scoped subagents, and disjoint writes are explicit and internally consistent. |
| `profile_artifacts` | 15 | Required profile artifacts are substantive; irrelevant frontend or hardware artifacts are not demanded. |
| `evidence_and_done` | 15 | `docs/implementation/EXECPLAN.md` is the concrete active plan governed by `PLANS.md` and contains target-specific milestones, evidence, validation, restart behavior, stop conditions, and done criteria. Do not count the `PLANS.md` contract template itself as an active plan. |
| `safety_boundaries` | 15 | Product runtime implementation is excluded; unsafe writes, secrets, external production, fabrication, energizing, deployment, and physical action remain human-gated where applicable. |
| `unresolved_risks` | 5 | Assumptions, unresolved decisions, caveats, provenance, skipped checks, and remaining risks are visible. |

## `commands_and_harness` passing branches

`commands_and_harness` remains mandatory. Award 3 or 4 only when concrete target
evidence satisfies exactly one branch:

1. **Existing product-runtime branch**
   - The claimed install, run/development, build, test, lint, format, type-check,
     integration, and end-to-end commands resolve to real runnable repository
     commands.
   - One truthful authoritative ordered gate resolves to those real commands and
     proves the applicable product behavior.
2. **Greenfield documentation-only branch**
   - The target explicitly states that product runtime implementation is out of
     scope for the current run.
   - Every absent product-command category is explicitly marked unavailable.
   - No replacement command is invented.
   - The generated handoff validator is runnable and clearly labeled as
     scaffold/handoff-integrity evidence only, never product behavior or product
     completion.
   - The first implementation milestone after any planning/consensus milestone is
     a blocking product-command bootstrap: it must define real product install,
     run/development, build, test, lint, format, type-check, integration, and
     end-to-end commands plus their authoritative ordered gate before downstream
     product implementation or any completion claim.
   - The handoff says product runtime implementation has not started and makes no
     product-complete claim.

All greenfield conditions are conjunctive. Fail this criterion if any one is
missing. Passing the generated handoff validator alone is never sufficient.

## Passing requirements

- `overall_pass` is true;
- weighted score is at least 80/100;
- every criterion appears exactly once;
- `commands_and_harness`, `evidence_and_done`, and `safety_boundaries` pass.

The grader must inspect only the target repository named in the evaluation prompt and must
not modify it.
