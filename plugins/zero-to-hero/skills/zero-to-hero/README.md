# zero-to-hero Codex skill

`zero-to-hero` prepares product repositories for later agent implementation. It
generates canonical requirements, capability-specific documentation, a
Codex-native harness, durable planning contracts, safe manifests, and neutral
handoff evidence. It supports software, hardware, and composite products.

It never implements target product runtime code and never authorizes production
or physical effects.

## Install and invoke

Install this directory as:

```txt
.agents/skills/zero-to-hero/
```

Invoke explicitly:

```txt
Use $zero-to-hero to prepare this repository for implementation. Generate
documentation, harness, plans, and handoff artifacts only; do not implement
product runtime code.
```

## Contract-driven workflow

`references/contract-graph.yaml` is the executable phase and prompt source of
truth. Output profiles under `references/output-profiles/` select exact required
and forbidden artifacts from repository evidence plus approved capability data.

Verify generated views:

```bash
python scripts/sync_contract_views.py .
python scripts/prompt_sequence_check.py .
```

## Preview and apply

The generator is dry-run by default:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo --profile auto
```

For a greenfield or interview-selected product family, provide approved
capability evidence:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --approved-capabilities-file /path/to/approved-capabilities.json
```

For capabilities already approved in a repository brief, bind direct tokens to
that exact evidence file. The brief must contain exactly one matching
machine-readable line, for example:

```text
Approved capability tokens: web_frontend, api_backend
```

Then run:

```bash
python3 scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --approved-capability web_frontend \
  --approved-capability api_backend \
  --approved-capability-source PRODUCT_BRIEF.md
```

Compose profiles by repeating `--profile`:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --profile robotics-product \
  --profile pcb-electronics
```

After reviewing the preview, write only into a clean, safe Git worktree:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --profile web-app --profile api-service --write
```

Existing files are preserved. Replacement is explicit and scoped:

```bash
python scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --profile web-app --write --force docs/ui/FRONTEND_CONTEXT.md
```

The only generated manifest is
`docs/00-meta/generated-files.manifest.yaml`.

After specializing generated documentation or after repository commands change,
run the bounded refresh recorded in that manifest:

```bash
python3 scripts/apply_zero_to_hero_templates.py /path/to/repo \
  --write --refresh-manifest
```

This preserves target-authored bytes outside exact machine-owned command
markers and does not require a clean tree or whole-file force.

To reproduce an unchanged committed handoff, run the manifest's recorded
command from the target repository root. Its lifecycle flag is:

```bash
python3 path/to/apply_zero_to_hero_templates.py . \
  --write --replay-manifest
```

Replay preserves the manifest's exact profile/provenance selection and refuses
changed approval evidence. Use a new explicit clean selection transaction for
approval changes.

## Optional adapters

- `scripts/omx_adapter.py` probes audited OMX compatibility. Compatible OMX
  creates and owns its runtime state from the neutral implementation brief;
  missing OMX falls back to native Codex or deterministic sequential execution.
- `scripts/text_to_cad_probe.py` probes the installed
  `earthtojake/text-to-cad` interface for mechanical and robotics geometry.
  STEP remains primary and physical actions stay human-authorized.

## Validation and distribution

From the repository that packages this skill, run the authoritative pinned gate:

```bash
make validate
```

For a standalone skill copy:

```bash
python scripts/zero_to_hero_check.py . --deep
python scripts/build_skill_zip.py . --out /tmp/zero-to-hero-skill.zip
```

Model-backed evaluations and external adapters report `PASS`, `SKIP`, or `FAIL`
separately. Unavailable tooling is never represented as a pass.
