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

Before product runtime exists, the generator provides:

```txt
python3 scripts/zero_to_hero_handoff_check.py .
```

That dependency-free command validates the embedded contract-selected artifact
set, manifest-record hashes, active ExecPlan structure, profile-negative
assertions, matching machine-owned command blocks, and staged plus unstaged Git
whitespace. It does not prove product behavior. Once real product checks exist,
the generated `AGENTS.md` composes this handoff check with an explicit
`verify:local-product` / `verify-local` gate or detected non-mutating quality
commands. Generic format aliases remain inventory only because they may rewrite
files. Never replace missing product evidence with a scaffold-only pass. When
any command category is unavailable, the active ExecPlan must place a blocking
product-command bootstrap immediately after planning consensus and before every
profile implementation milestone. That bootstrap defines real install,
run/development, build, test, lint, format, type-check, integration,
end-to-end, and authoritative ordered-gate commands.

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
