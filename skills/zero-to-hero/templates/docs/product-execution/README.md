# Product Execution Harness

This directory proves that the product is usable, not only visually complete.

Select contracts that match the product surface:

- action-binding matrix mapping every visible or callable control to behavior;
- form/command lifecycle and validation states;
- dataflow and transaction boundaries;
- deterministic scenario seeds using synthetic data;
- local simulators for external providers and physical effects;
- negative paths, cancellation, timeout, retry, and recovery;
- role-based walkthroughs and accessibility proof;
- runtime evidence paths and retention policy;
- one local product done gate composed from actual repository commands.

## Evidence contract

For each priority workflow record:

| Workflow | Preconditions | Action | Observable result | Negative path | Evidence |
| --- | --- | --- | --- | --- | --- |
| Primary approved journey | deterministic local entrypoint | visible successful result | deterministic empty/error/retry states | integration plus end-to-end evidence | approved product owner |

Evidence must be reproducible and may not contain credentials, production data,
or real PII. A mocked, skipped, or unavailable integration is labeled as such;
it is not equivalent to a passing live integration.

## External-effect boundary

Local Mode uses deterministic local services, synthetic data, and mocked or
sandboxed providers. Production writes, deployment, fabrication, flashing,
energizing, and physical actuation require separate explicit authorization.
