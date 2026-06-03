# Harness pack

Generate frontend parity, product usability, runtime evidence, traceability, local simulators, role walkthroughs, negative paths, observability, and local done gates.

## Required evidence

- phase input artifacts are present;
- generated outputs are listed in the generated-file manifest;
- decisions are recorded as explicit, inferred, unresolved, rejected, or out_of_scope;
- validation checks for this phase pass or unresolved blockers are recorded.

## Stop conditions

Stop when required user decisions are missing, when generated artifacts would encode unsafe assumptions, or when product implementation code would need to be changed.
