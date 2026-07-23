# Artifact lifecycle

Artifacts move through these states:

```txt
proposed → reviewed → canonical → superseded → archived
```

Generated visuals are proposed until approved and deconstructed into contracts.
The neutral implementation brief and planning evidence become canonical only
after explicit consensus. CLI-owned OMX state is an execution derivative, not
source of truth. Runtime evidence under `.artifacts` is review evidence, not
source of truth.

Do not delete superseded content unless cleanup can preserve substance elsewhere or the user explicitly approves removal.
