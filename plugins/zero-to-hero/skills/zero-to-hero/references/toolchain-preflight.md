# Toolchain preflight

Use `scripts/toolchain_preflight.py` to inventory local tools before a zero-to-hero run or before handoff to implementation agents.

The preflight is advisory. It does not install tools, run app code, enable external effects, or mutate product source files.

Resolve one maintenance interpreter before invoking any skill script:

- prefer `ZERO_TO_HERO_PYTHON` when the caller supplies it;
- otherwise select Python 3.10 or newer with the repository-pinned PyYAML and
  jsonschema dependencies available;
- reuse the exact selected executable throughout the run;
- treat a missing compatible interpreter or dependency as a blocker instead of
  retrying arbitrary host interpreters.

It checks for common command families:

- core repo tools: `git`, `python3`, `node`, `npm`;
- JavaScript package managers: `pnpm`, `yarn`, `bun`;
- containers and task runners: `docker`, `docker-compose`, `make`, `just`;
- frontend evidence tools: Playwright/Storybook config signals;
- infrastructure tools: `terraform`, `kubectl`, cloud CLIs;
- hardware tools: `kicad-cli`, `openscad`, `freecad`, `platformio`.

Examples:

```bash
python scripts/toolchain_preflight.py /path/to/repo
python scripts/toolchain_preflight.py /path/to/repo --write
```

When `--write` is used, reports are written to:

```txt
.codex/reports/zero-to-hero/toolchain-preflight.json
.codex/reports/zero-to-hero/toolchain-preflight.md
```

Missing tools are not always blockers. They should be interpreted against the detected capabilities and the planned output profile.
