## Summary

Describe the change and why it is needed.

## Scope

- [ ] Skill instructions / prompts
- [ ] References / templates
- [ ] Scripts / validation
- [ ] Plugin metadata / release packaging
- [ ] Documentation only

## Safety checklist

- [ ] This does not add target-product runtime implementation behavior.
- [ ] This does not weaken prompt-injection or instruction-trust handling.
- [ ] This does not add unbounded or side-effectful default checks.
- [ ] This does not create generated/runtime artifacts in the repo.
- [ ] Source skill and plugin mirror are synchronized.

## Validation

Paste the relevant commands and results:

```bash
make validate
make archive
```

## Release impact

- [ ] No release impact.
- [ ] Release metadata or archive behavior changed.
- [ ] Documentation updated for release behavior.
