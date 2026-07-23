# Data and ML requirements

## Data contract

| Dataset or stream | Owner | Schema/version | Freshness | Classification |
| --- | --- | --- | --- | --- |
| Every approved dataset or stream | named accountable owner | versioned schema with compatibility policy | explicit freshness objective | public, internal, confidential, or restricted |

Document lineage, allowed uses, consent, retention, deletion, partitioning,
quality rules, and train/validation/test separation where applicable.
Keep the source lineage ownership map canonical and link every derived dataset
or model artifact back to its accountable source owner.

### Schema, quality, and privacy policy

Each schema version declares required fields, types, nullability, identifiers,
compatibility rules, and the owner who may approve a breaking change. Quality
rules define measurable completeness, uniqueness, validity, freshness, and
referential-integrity thresholds plus quarantine behavior. The privacy policy
maps every classified field to its allowed purpose, consent basis, access
boundary, masking rule, retention period, deletion procedure, and audit owner.
Promotion fails when any schema, quality, or privacy rule is unknown or
breached.

## Pipeline behavior

- Ingestion and backfill: bounded, observable, resumable, and isolated from live
  promotion.
- Idempotency and deduplication: stable source identity prevents duplicate
  effects.
- Late, missing, corrupt, and out-of-order data: quarantine or reconcile by an
  explicit policy.
- Checkpoint/restart behavior: checkpoints identify exact source offsets and
  schema versions.
- Reprocessing and rollback: preserve lineage and make the affected partitions
  reviewable before replacement.

## Model lifecycle when applicable

- Feature and label definitions: version semantics, leakage exclusions, and
  ownership.
- Reproducible training inputs and seeds: pin data snapshots, code, environment,
  and randomness.
- Baseline and promotion thresholds: compare against a recorded baseline on
  representative slices.
- Drift and bias monitoring: define slice metrics, alert thresholds, and a
  rollback owner.
- Model/data version linkage: every artifact records exact input and evaluator
  versions.

## Validation and operations

- Reproducible local run: record the exact locked command, deterministic fixture,
  environment, and random seed.
- Evaluation and versioning: record datasets, metrics, thresholds, evaluator
  versions, and promotion results.
- Drift detection plan: define the baseline window, thresholds, alert, and
  response owner.
- Schema and quality checks: fail on incompatible schemas and breached quality
  constraints.
- Small deterministic fixture: cover happy, missing, duplicate, corrupt, and
  late records.
- Integration/backfill smoke check: use an isolated bounded partition.
- Reconciliation and observability: compare source, processed, and published
  counts with traceable discrepancies.
- Failure alert and recovery owner: every blocking failure has an accountable
  responder and replay procedure.

Production data access, destructive migrations, and model promotion require
separate authorized execution; this contract only prepares the handoff.
