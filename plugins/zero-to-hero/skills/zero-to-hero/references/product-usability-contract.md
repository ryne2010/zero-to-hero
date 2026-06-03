# Product Usability Contract

This layer prevents beautiful but unusable apps.

## Required artifacts

```txt
docs/product-execution/
  app-usability-contract.md
  action-binding.schema.yaml
  action-binding-matrix.yaml
  workflow-transaction.schema.yaml
  workflow-transactions/
  dataflow-contract.schema.yaml
  dataflows/
  form-lifecycle.schema.yaml
  forms/
  scenario-seed.schema.yaml
  scenarios/
  route-capability-acceptance.yaml
  local-mode-service-contracts.md
  no-dead-ends-policy.md
  workflow-evidence-policy.md
```

## Key rule

Every visible control must map to one of:

```txt
implemented action
explicit disabled state with reason
purely decorative element marked non-interactive
```

## Required checks

- action binding check
- form lifecycle check
- scenario fixture check
- no-dead-controls check
