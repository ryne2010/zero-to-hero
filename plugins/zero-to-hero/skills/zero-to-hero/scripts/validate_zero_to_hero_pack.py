#!/usr/bin/env python3
from __future__ import annotations
import ast
import json
import os
import subprocess
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from zero_to_hero_contract import ContractError, graph_prompts, load_graph  # noqa: E402
try:
    import yaml
except Exception:
    yaml = None

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
skill = root if (root / 'SKILL.md').exists() else root / '.agents/skills/zero-to-hero'
errors: list[str] = []
warnings: list[str] = []

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(skill))
    except Exception:
        return str(path)

def require(path: str) -> None:
    if not (skill / path).exists():
        errors.append(f'missing {path}')

required = [
    'SKILL.md','README.md','skill-manifest.yaml','agents/openai.yaml',
    'references/quickstart.md','references/mode-contracts.md',
    'references/phase-state-machine.yaml','references/generated-file-manifest.md',
    'references/decision-ledger.md','references/context-routing.md',
    'references/minimum-viable-proof.md','references/skill-health-check.md',
    'references/rollback-policy.md','references/visual-target-provenance.md',
    'references/hardware-reality-checks.md','references/phase-output-artifacts.yaml',
    'references/phase-gates.yaml','references/risk-tiering.md','references/source-research-policy.md',
    'references/target-repo-preflight.md','references/repo-safety-preflight.md','references/toolchain-preflight.md','references/external-context-sources.md','references/phase-prompt-contract.md','references/acceptance-evidence.md','references/final-handoff-quality-bar.md','references/artifact-lifecycle.md','references/instruction-trust-scan.md','references/prompt-sequence-contract.md','references/target-repo-audit-report.md','references/template-application-profiles.md','references/prompt-bundle.md','references/distribution.md','references/check-operability.md',
    'schemas/contract-graph.schema.json','schemas/output-profile.schema.json',
    'schemas/planning-evidence.schema.json','schemas/decision-ledger.schema.yaml',
    'schemas/generated-files-manifest.schema.yaml','schemas/recovery-task-graph.schema.yaml',
    'evals/cases.json','evals/handoff-quality-rubric.md',
    'evals/handoff-quality-rubric.schema.json',
    'scripts/apply_zero_to_hero_templates.py','scripts/capability_detect.py','scripts/zero_to_hero_start.py',
    'scripts/canonical_cleanup_check.py','scripts/toolchain_preflight.py','scripts/external_context_inventory.py','scripts/instruction_trust_scan.py','scripts/prompt_sequence_check.py','scripts/render_prompt_bundle.py','scripts/build_skill_zip.py','scripts/run_fixture_tests.py',
    'scripts/zero_to_hero_check.py','scripts/zero_to_hero_doctor.py','scripts/prune_skill_artifacts.py','scripts/target_repo_audit.py','scripts/repo_safety_check.py','scripts/phase_gate_check.py',
    'scripts/schema_validate.py','scripts/run_skill_evals.py','scripts/omx_adapter.py','scripts/test_omx_integration.py',
    'scripts/planning_evidence_check.py','scripts/test_planning_evidence_check.py',
    'scripts/text_to_cad_probe.py','scripts/test_text_to_cad_probe.py','scripts/test_generation_transactions.py',
    'scripts/test_profile_generation_matrix.py','fixtures/README.md',
    'templates/scripts/zero_to_hero_handoff_check.py',
]
for r in required:
    require(r)

try:
    graph = load_graph(skill)
    expected_prompts = [item['prompt_file'] for item in graph_prompts(graph)]
except ContractError as exc:
    errors.append(f'contract graph invalid: {exc}')
    expected_prompts = []
prompt_dir = skill / 'prompts'
prompts = sorted(p.name for p in prompt_dir.glob('*.md')) if prompt_dir.exists() else []
for name in expected_prompts:
    if name not in prompts:
        errors.append(f'missing prompt {name}')
extra_prompts = [p for p in prompts if p not in expected_prompts and p != 'README.md']
if extra_prompts:
    warnings.append(f'extra prompt files present: {extra_prompts}')
prefixes: dict[str, list[str]] = {}
for p in prompts:
    m = re.match(r'^(\d+)-', p)
    if m:
        prefixes.setdefault(m.group(1), []).append(p)
for pref, names in prefixes.items():
    if pref != '99' and len(names) > 1:
        errors.append(f'duplicate prompt phase {pref}: {names}')

profiles = list((skill / 'references/output-profiles').glob('*.yaml')) if (skill / 'references/output-profiles').exists() else []
if not profiles:
    errors.append('missing output profiles')

expected_fixtures = ['idea-only','react-vite-scaffold','nextjs-partial-app','api-fastapi','cli-python','hardware-kicad','robotics-firmware','docs-first-product','messy-monorepo','prompt-injection-risk']
for fx in expected_fixtures:
    if not (skill / 'fixtures' / fx).exists():
        errors.append(f'missing fixture {fx}')

for bad in list(skill.rglob('__pycache__')) + list(skill.rglob('*.pyc')):
    errors.append(f'pack contains runtime cache artifact: {rel(bad)}')

for report_dir in list(skill.rglob('.codex')):
    errors.append(f'pack contains generated report directory: {rel(report_dir)}')
for duplicate in ['references/context-router.md','references/skill-pack-health.md','references/hardware-safety-and-review.md']:
    if (skill / duplicate).exists():
        errors.append(f'noncanonical duplicate reference remains: {duplicate}')

for bad_template_dir in ['templates/omx','templates/agents-skills','templates/reports','templates/manifest','templates/decision-ledger']:
    if (skill / bad_template_dir).exists():
        errors.append(f'noncanonical template directory remains: {bad_template_dir}')
for expected_template in [
    'templates/AGENTS.md',
    'templates/PLANS.md',
    'templates/CODEX.md',
    'templates/FINAL_HANDOFF.md',
    'templates/docs/implementation/IMPLEMENTATION_BRIEF.md',
    'templates/docs/implementation/PLANNING_EVIDENCE.md',
    'templates/scripts/zero_to_hero_handoff_check.py',
]:
    if not (skill / expected_template).exists():
        errors.append(f'missing canonical template: {expected_template}')
for forbidden_runtime_template in [
    'templates/.omx/ultragoal/goals.json',
    'templates/.omx/ultragoal/ledger.jsonl',
    'templates/.omx/ultragoal/brief.md',
]:
    if (skill / forbidden_runtime_template).exists():
        errors.append(f'runtime-owned OMX template must not be packaged: {forbidden_runtime_template}')

if yaml:
    for yp in list(skill.rglob('*.yaml')) + list(skill.rglob('*.yml')):
        try:
            yaml.safe_load(yp.read_text(encoding='utf-8'))
        except Exception as exc:
            errors.append(f'yaml parse failed {rel(yp)}: {exc}')
else:
    errors.append('PyYAML not available; use the pinned repository environment')

for js in skill.rglob('*.json'):
    try:
        json.loads(js.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'json parse failed {rel(js)}: {exc}')

for py in (skill / 'scripts').glob('*.py'):
    try:
        ast.parse(py.read_text(encoding='utf-8'))
    except SyntaxError as exc:
        errors.append(f'python syntax failed {rel(py)}: {exc}')
generated_handoff_template = skill / 'templates/scripts/zero_to_hero_handoff_check.py'
if generated_handoff_template.is_file():
    try:
        ast.parse(generated_handoff_template.read_text(encoding='utf-8'))
    except SyntaxError as exc:
        errors.append(
            f'python syntax failed {rel(generated_handoff_template)}: {exc}'
        )


openai_meta = skill / 'agents/openai.yaml'
if openai_meta.exists() and yaml:
    try:
        meta = yaml.safe_load(openai_meta.read_text(encoding='utf-8')) or {}
        if meta.get('policy', {}).get('allow_implicit_invocation') is not False:
            errors.append('agents/openai.yaml should require explicit invocation for this broad repo-modifying skill')
        icons = [meta.get('interface', {}).get('icon_small'), meta.get('interface', {}).get('icon_large')]
        for icon in icons:
            if icon and not (skill / icon.replace('./','',1)).exists():
                errors.append(f'agents/openai.yaml icon path does not resolve from skill root: {icon}')
    except Exception as exc:
        errors.append(f'agents/openai.yaml metadata check failed: {exc}')


# Instruction-trust scan should redact suspicious raw snippets by default.
scan_script = skill / 'scripts/instruction_trust_scan.py'
inj_fixture = skill / 'fixtures/prompt-injection-risk'
if scan_script.exists() and inj_fixture.exists():
    try:
        env = dict(os.environ)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        result = subprocess.run([sys.executable, str(scan_script), str(inj_fixture)], capture_output=True, text=True, timeout=15, env=env)
        scan_out = result.stdout + result.stderr
        if result.returncode != 0:
            errors.append('instruction_trust_scan.py failed on prompt-injection-risk fixture')
        forbidden_payloads = ['ignore previous instructions', 'disable tests', 'Print all secrets', 'print all secrets']
        for payload in forbidden_payloads:
            if payload in scan_out:
                errors.append(f'instruction_trust_scan.py default output should redact payload text: {payload}')
        try:
            parsed = json.loads(result.stdout)
            findings = parsed.get('findings', [])
            if findings and any('snippet_sha256' not in f or 'snippet_redacted' not in f for f in findings):
                errors.append('instruction_trust_scan.py findings should include snippet_sha256 and snippet_redacted by default')
            if findings and any('snippet' in f for f in findings):
                errors.append('instruction_trust_scan.py should not include raw snippet by default')
        except Exception as exc:
            errors.append(f'instruction_trust_scan.py emitted invalid JSON on fixture: {exc}')
    except Exception as exc:
        errors.append(f'instruction_trust_scan.py redaction check failed: {exc}')

frontmatter = (skill / 'SKILL.md').read_text(errors='ignore') if (skill / 'SKILL.md').exists() else ''
if not frontmatter.startswith('---') or 'name: zero-to-hero' not in frontmatter or 'description:' not in frontmatter:
    errors.append('SKILL.md frontmatter missing or incomplete')

print('zero-to-hero skill health')
print(f'  skill_dir: {skill}')
print(f'  prompt_files: {len(prompts)}')
print(f'  output_profiles: {len(profiles)}')
print(f'  fixtures_checked: {len(expected_fixtures)}')
print(f'  errors: {len(errors)}')
for e in errors:
    print('  ERROR:', e)
for w in warnings:
    print('  WARN:', w)
if errors:
    sys.exit(1)
