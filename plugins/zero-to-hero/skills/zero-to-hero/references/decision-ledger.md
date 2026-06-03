# Decision ledger

Use a decision ledger to prevent inferred behavior from silently becoming product policy.

Allowed decision states:

```txt
explicit
inferred
unresolved
rejected
out_of_scope
```

Canonical path:

```txt
docs/00-meta/decision-ledger.yaml
```

Example:

```yaml
decisions:
  - id: ui.default_theme
    status: explicit
    value: light mode default
    source: user
  - id: dashboard.export_behavior
    status: inferred
    value: opens export menu
    requires_approval: true
  - id: payment_provider
    status: unresolved
    blocks:
      - billing_integration_pack
```

Generated visuals must never create `explicit` decisions unless the user approves the visual and the behavior is deconstructed into a contract.
