# API service requirements

## Contract inventory

| Surface | Consumers | Authentication | Idempotency | Version policy |
| --- | --- | --- | --- | --- |
| Every approved endpoint | named first-party and external consumers | explicit per route; deny by default when identity is required | required for retried mutations | versioned schema with documented deprecation |

### Interface and schema contracts

For every interface, define the transport, method, route or topic, request and
response schema, status codes, pagination, filtering, ordering, rate limits,
timeouts, retry safety, and deprecation behavior. Keep the machine-readable API
description canonical and link each inventory row to its operation identifier
and schema version. Generated clients, examples, and prose are subordinate to
that description; incompatible behavior requires a new version and migration
window.

## Data and consistency

- Transaction boundaries: each mutation defines its atomicity and rollback
  boundary.
- Concurrency and duplicate-request behavior: retries are safe, and conflicting
  writes produce a deterministic conflict response.
- Validation and normalization: schemas reject unknown or invalid data before
  side effects and normalize only documented fields.
- Migration and backward-compatibility policy: additive changes are preferred;
  breaking changes require a version and migration window.

## Failure contract

Document invalid input, unauthenticated, unauthorized, missing, conflict,
rate-limited, dependency failure, timeout, and internal-error responses. Error
payloads must be stable, safe to expose, and traceable without leaking secrets.

## Security and privacy

- Trust boundaries and authorization checks: authenticate at the boundary and
  authorize the concrete resource action server-side.
- Secret and credential handling: load secrets from approved runtime providers;
  never return or log them.
- PII classification and retention: classify each field and keep it only for
  the approved lifetime.
- Abuse controls and audit events: rate-limit risky operations and record
  security-relevant decisions without sensitive payloads.

## Operations and proof

- Local integration command: use the exact target-specific command identified
  as `integration` in root `AGENTS.md`. It must exercise real local adapters
  against synthetic or inert dependencies, perform no production effect, and
  exit nonzero when setup or assertions fail.
- Contract-test command: use the exact target-specific command identified as
  `test` or `integration` in root `AGENTS.md`. It must validate the canonical
  interface description, compatibility rules, request/response examples, auth
  denials, error schemas, retry behavior, and idempotent replay.
- Health/readiness behavior: distinguish process liveness from dependency
  readiness without leaking configuration.
- Structured logs, metrics, and traces: correlate requests and failures with
  redacted identifiers.
- Contract, integration, and end-to-end checks: validate schemas, real boundary
  adapters, and the primary user journey.
- Load and resilience targets: record approved latency, concurrency, timeout,
  and recovery thresholds before release.
- Local-mode providers and production-effect gates: local checks use inert
  providers; live mutations require explicit downstream authority.

No live provider calls, production mutations, or deployment actions are
authorized by this document.
