# Codex handoff

Use this repository through a planning-first workflow.

Recommended sequence:

```txt
$deep-interview when product intent is incomplete
$ralplan for planning and task-graph generation
$ultragoal for long-running aggregate execution
$ralph for final review and fix pressure
```

Do not start implementation until the source-of-truth map, decision ledger, and relevant harness contracts are present.

Keep sandboxing strict. Real providers, secrets, production data, and external effects must remain disabled until explicit gates pass.
