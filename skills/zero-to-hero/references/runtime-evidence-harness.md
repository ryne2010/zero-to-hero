# Runtime Evidence Harness

A user story is not done until runtime evidence proves it.

Capture:

```txt
before state
user actions
queries/mutations/service calls
domain events
audit events
local provider simulator events
UI feedback
after state
state after reload
screenshots/traces
console/network cleanliness
```

Recommended directory:

```txt
.artifacts/
  screenshots/
  traces/
  workflow-evidence/
  reports/
```

Keep runtime artifacts ignored unless the repo intentionally commits golden baselines.
