# Target Repo Pre-Mortem

Before generating implementation tasks, forecast why the agentic build could fail.

## Required questions

```txt
If Codex/OMX fails to turn this repo into a production-ready local app, why will it fail?
Where will it infer too much?
Where will it build a scaffold instead of a product?
Where will controls be dead?
Where will forms fail?
Where will data not persist?
Where could safety boundaries be weakened?
Where could untrusted content become instructions?
Where could final review claim completion without evidence?
```

## Outputs

```txt
.codex/reports/zero-to-hero/premortem.md
.codex/reports/zero-to-hero/failure-mode-register.yaml
```
