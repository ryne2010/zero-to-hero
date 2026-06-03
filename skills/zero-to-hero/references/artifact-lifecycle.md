# Artifact lifecycle

Artifacts move through these states:

```txt
proposed → reviewed → canonical → superseded → archived
```

Generated visuals are proposed until approved and deconstructed into contracts. Plans under `.omx/plans` are non-canonical until approved by the user. Runtime evidence under `.artifacts` is review evidence, not source of truth.

Do not delete superseded content unless cleanup can preserve substance elsewhere or the user explicitly approves removal.
