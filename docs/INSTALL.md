# Install

## Project-scoped skill install

```bash
gh skill install ./skills/zero-to-hero --agent codex --scope project
```

## Manual install into a target repo

```bash
mkdir -p /path/to/repo/.agents/skills
cp -R skills/zero-to-hero /path/to/repo/.agents/skills/zero-to-hero
```

## Plugin wrapper

The installable plugin wrapper is under:

```text
plugins/zero-to-hero/
```
