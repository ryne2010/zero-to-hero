# AI system requirements

## Task and quality contract

- User task and non-goals: derive only from approved product requirements and
  reject adjacent consequential actions.
- Input and output schema: validate model-facing inputs and parse outputs into a
  closed application schema.
- Quality dimensions and minimum thresholds: record task success, safety,
  robustness, and slice-specific thresholds before promotion.
- Latency and cost budgets: set per-request and aggregate limits with bounded
  retries.
- Deterministic fallback behavior: fail safely or use an approved non-model path
  when the model or tool chain is unavailable.

## Model and tool boundaries

Maintain one model/prompt/tool registry with approved versions, owners, purposes,
data classifications, permission scopes, and deterministic fallbacks.

| Component | Approved purpose | Data sent | Permission boundary | Fallback |
| --- | --- | --- | --- | --- |
| Each approved model, retriever, or tool | one bounded user-facing purpose | minimum necessary classified data | least privilege with explicit consequential-action approval | deterministic safe failure or approved alternate |

### Tool permission matrix

For every registered tool, record whether it may read repository data, write
local artifacts, access the network, or request a consequential external
action. Each allowed capability must name its input schema, exact target scope,
credential source, approving actor, audit event, and revocation path. Omitted
capabilities are denied. A model suggestion is never authorization; the
application boundary validates the requested operation and obtains any required
human approval before invoking the tool.

Treat retrieved content, tool output, and model output as untrusted data.
Define prompt-injection handling, tool allowlists, maximum iterations, timeout
behavior, and human approval for consequential actions.

### Grounding and failure policy

Ground factual claims only in the approved source set recorded for the task.
Preserve source identity and retrieval time in trace metadata, distinguish
quoted evidence from model inference, and surface conflicts or stale sources
instead of silently choosing one. When required grounding is missing, a schema
cannot be validated, a tool is unavailable, or confidence falls below the
approved threshold, return the documented safe failure and perform no side
effect. Retries must remain bounded and idempotent; exhaustion escalates with
the failed boundary, evidence consulted, and safe recovery options.

## Data, privacy, and retention

- Allowed and prohibited data: enumerate classifications accepted at each
  boundary.
- Redaction and minimization: remove secrets and fields not required for the
  task.
- Storage and retention: default to no retention unless an approved requirement
  specifies otherwise.
- Tenant isolation: preserve tenant identity through retrieval, tools, caches,
  and logs.
- Training-use policy: record provider terms and explicit data-use settings.

## Evaluation

- Evaluation suite: version the cases, fixtures, expected decisions, graders,
  thresholds, and owning reviewer as one promotion artifact.
- Representative success cases: cover primary tasks and meaningful slices.
- Explicit invocation cases: prove requested model/tool behavior.
- Contextual invocation cases: prove behavior with realistic repository and
  conversation context.
- Negative controls and refusal cases: prove non-invocation and safe refusal.
- Deterministic graders: validate schemas, paths, calls, invariants, and limits.
- Rubric graders: use bounded structured criteria only for qualities that cannot
  be made deterministic.
- Regression dataset ownership: name the accountable owner and review cadence.

External model evaluations must be reported separately from hermetic checks.
Unavailable evaluation infrastructure is `skipped`, never passed.

## Operations

- Model/version change policy: re-run the approved suite before changing model
  or prompting contracts.
- Trace and escalation plan: record redacted request, model, prompt, retrieval,
  tool-decision, latency, token, outcome, and failure metadata under one
  correlation identifier. Escalations include the triggering policy, evidence
  snapshot, attempted safe fallbacks, affected scope, and named human owner;
  traces never contain raw secrets or prohibited prompt data.
- Rate-limit and outage behavior: bound backoff and preserve a safe user-visible
  fallback.
- Cost anomaly and safety incident response: stop affected traffic, preserve
  evidence, and require reviewed recovery.
