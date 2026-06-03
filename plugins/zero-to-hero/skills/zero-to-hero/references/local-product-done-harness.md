# Local Product Done Harness

Local Mode must be a complete product surface with synthetic data and mocked/sandboxed integrations. It must not be a static demo.

## Required harness layers

```txt
runtime evidence
coverage and traceability
local provider simulators
brownfield inventory
state machines
negative paths
role walkthroughs
observability
acceptance evidence directory
single local product done command
```

## Suggested top-level gate

```txt
npm run verify:local-product
make verify-local
just verify-local
```

The command should prove:

```txt
visual parity
product usability
workflow completion
role walkthroughs
negative paths
local provider simulator behavior
no real-world effects
runtime evidence
production delta documented
```

## Universal local verification target

Every product repo should define one local verification target appropriate for its stack:

```txt
npm run verify:local-product
make verify-local
just verify-local
pytest + playwright + local services
make verify-hardware-pack
```

The command should prove the local product surface is usable without real-world effects. For non-app repos, define an equivalent local proof target.
