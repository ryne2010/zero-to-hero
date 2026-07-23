# Infrastructure requirements

## Environments and ownership

| Environment | Purpose | Change authority | Data class | Promotion gate |
| --- | --- | --- | --- | --- |
| local | deterministic development | repository owner | synthetic | local checks |
| Every non-local environment | one approved lifecycle purpose | named human or automation identity | explicit classification; no production data in local fixtures | reviewed plan, policy checks, and environment-specific approval |

Keep this environment matrix current for every allowed lifecycle stage and
block promotion to an undeclared environment.

## Desired-state contract

- Regions, accounts/projects, and tenancy: enumerate isolation and residency
  requirements before provisioning.
- Network and trust boundaries: default deny and expose only reviewed ingress
  and egress.
- Compute, storage, and managed dependencies: pin ownership, lifecycle, quotas,
  and failure behavior.
- Identity, roles, and least privilege: separate plan, apply, runtime, and break-
  glass identities.
- Secrets and key rotation: use an approved secret manager and tested rotation
  procedure.
- Backup, restore, retention, and disaster recovery: prove restoration against
  explicit recovery objectives.

## Change safety

The generated root `AGENTS.md` is the command authority. Before handoff, resolve
each required row below to one copyable target-native invocation with no
placeholder tokens.

| Command class | Required behavior |
| --- | --- |
| Format command | checks canonical formatting and exits nonzero on a diff |
| Validate command | parses configuration, schemas, modules, and references without mutation |
| Plan command | produces a read-only preview scoped to the declared environment |
| Test command | exercises policies, modules, and local or emulated contracts without live infrastructure |

- Plan/preview command: exact read-only preview is the first required evidence.
- Policy and static checks: block public exposure, excess privilege, unencrypted
  data, and unbounded resources.
- Drift detection: compare deployed state to versioned desired state without
  silently reconciling.
- Rollback or roll-forward: define the safe recovery per resource class.
- State locking and interrupted-run recovery: prevent concurrent mutation and
  preserve an auditable recovery path.
- Cost and quota guardrails: set owner-approved budgets and hard ceilings.

No apply, deployment, production mutation, DNS change, or secret rotation is
authorized by this document. Those actions require a separate explicit approval
against a reviewed plan.

### Deployment authorization gate

The deployment authorization gate remains closed until the exact environment,
reviewed plan digest, change ticket, approver identity, credential scope,
maintenance window, monitoring owner, and rollback trigger are recorded
together. Authorization applies only to that plan and window; a changed plan,
drift, missing policy evidence, or expired approval closes the gate. Local
validation never satisfies or bypasses this deployment gate.

## Reliability and evidence

- Availability and recovery objectives: state measurable service, recovery-
  time, and recovery-point targets.
- Metrics, logs, traces, and alerts: cover saturation, errors, dependency health,
  security events, and cost.
- Local/emulated integration proof: exercise configuration and contracts without
  live mutation.
- Ephemeral-environment proof: create and destroy only with explicit scoped
  authority.
- Security and compliance evidence: link policy output, threat decisions, and
  exception owners.
- Authoritative readiness command: use the target-specific done command from
  `AGENTS.md`.
