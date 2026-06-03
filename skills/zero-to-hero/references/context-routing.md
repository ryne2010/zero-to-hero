# Context routing

Large docs packs overwhelm implementation agents when every task tells them to read everything. Generate short context-router files that point agents to the right subset.

Recommended files:

```txt
docs/AGENT_CONTEXT.md
docs/ui/FRONTEND_CONTEXT.md
docs/product-execution/LOCAL_PRODUCT_CONTEXT.md
docs/hardware/HARDWARE_CONTEXT.md
docs/implementation/IMPLEMENTATION_CONTEXT.md
```

Each context file should include:

```txt
Read these first.
Read these only when the task requires them.
Do not read the entire docs tree for every small task.
Do not treat archived/out-of-scope documents as source of truth.
```

Context routing is a harness primitive, not a convenience.

## Required router outputs

When the repo has enough docs to overwhelm a normal implementation task, generate short first-read context routers. Common router files are:

```txt
docs/AGENT_CONTEXT.md
docs/ui/FRONTEND_CONTEXT.md
docs/product-execution/LOCAL_PRODUCT_CONTEXT.md
docs/hardware/HARDWARE_CONTEXT.md
docs/implementation/IMPLEMENTATION_CONTEXT.md
```

Each router should list only the canonical files required for a task family and explicitly mark archived/out-of-scope docs as non-authoritative.
