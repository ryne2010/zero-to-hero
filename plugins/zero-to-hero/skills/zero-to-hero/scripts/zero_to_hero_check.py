#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

from zero_to_hero_contract import ContractError, graph_prompts, load_graph  # noqa: E402

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

REQUIRED = [
    'SKILL.md','README.md','QUICKSTART.md','manifest.json','skill-manifest.yaml',
    'references/contract-graph.yaml','schemas/contract-graph.schema.json',
    'references/phase-state-machine.yaml','references/phase-gates.yaml',
    'references/output-profiles/web-app.yaml','references/decision-ledger.md',
    'references/generated-file-manifest.md','references/cleanup-allowlist.md',
    'references/target-repo-preflight.md','references/repo-safety-preflight.md',
    'references/external-context-sources.md','references/phase-prompt-contract.md',
    'references/operating-recipes.md','references/proof-first-implementation.md',
    'references/final-stability-notes.md',
    'schemas/contract-graph.schema.json','schemas/output-profile.schema.json',
    'schemas/planning-evidence.schema.json','schemas/decision-ledger.schema.yaml',
    'schemas/generated-files-manifest.schema.yaml',
    'schemas/recovery-task-graph.schema.yaml',
    'evals/cases.json','evals/handoff-quality-rubric.md',
    'evals/handoff-quality-rubric.schema.json',
    'scripts/validate_zero_to_hero_pack.py','scripts/run_fixture_tests.py',
    'scripts/target_repo_audit.py','scripts/repo_safety_check.py','scripts/zero_to_hero_start.py',
    'scripts/toolchain_preflight.py','scripts/external_context_inventory.py',
    'scripts/instruction_trust_scan.py','scripts/prompt_sequence_check.py',
    'scripts/render_prompt_bundle.py','scripts/build_skill_zip.py',
    'scripts/zero_to_hero_contract.py','scripts/sync_contract_views.py',
    'scripts/schema_validate.py','scripts/run_skill_evals.py',
    'scripts/omx_adapter.py','scripts/test_omx_integration.py',
    'scripts/planning_evidence_check.py','scripts/test_planning_evidence_check.py',
    'scripts/text_to_cad_probe.py','scripts/test_text_to_cad_probe.py',
    'scripts/test_generation_transactions.py','scripts/test_profile_generation_matrix.py',
    'references/omx-compatibility.md','references/text-to-cad-compatibility.md',
    'templates/PLANS.md','templates/scripts/zero_to_hero_handoff_check.py',
]
DEEP_REQUIRED = [
    'references/output-profiles/api-service.yaml','references/output-profiles/pcb-electronics.yaml',
    'references/output-profiles/firmware-iot.yaml','references/output-profiles/mobile-app.yaml',
    'references/output-profiles/desktop-app.yaml','references/output-profiles/robotics-product.yaml',
    'references/skill-health-check.md','references/check-operability.md','references/template-application-profiles.md',
    'references/instruction-trust-scan.md','references/external-context-sources.md','references/visual-target-provenance.md',
    'references/hardware-reality-checks.md','references/minimum-viable-proof.md',
    'fixtures/react-vite-scaffold/package.json','fixtures/api-fastapi/pyproject.toml',
    'fixtures/hardware-kicad/project.kicad_pro','fixtures/prompt-injection-risk/README.md',
]


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or '.').resolve()
    if (root / 'SKILL.md').exists():
        return root
    candidate = root / '.agents' / 'skills' / 'zero-to-hero'
    if (candidate / 'SKILL.md').exists():
        return candidate
    return root


def exists_checks(skill: Path, rels: list[str]) -> list[dict]:
    return [{'check': f'exists:{rel}', 'ok': (skill / rel).exists()} for rel in rels]


def prompt_inventory(skill: Path, graph: dict) -> dict:
    prompts = sorted((skill / 'prompts').glob('*.md')) if (skill / 'prompts').exists() else []
    names = [p.name for p in prompts if p.name != 'README.md']
    expected = [item['prompt_file'] for item in graph_prompts(graph)]
    missing = [name for name in expected if name not in names]
    extra = [name for name in names if name not in expected]
    actual_order = [name for name in names if name in expected]
    expected_order = [name for name in expected if name in names]
    return {
        'check': 'prompt_sequence',
        'ok': not missing and not extra and actual_order == expected_order,
        'prompt_count': len(names),
        'expected_count': len(expected),
        'missing': missing,
        'extra': extra,
        'order_matches_contract': actual_order == expected_order,
    }


def no_runtime_artifacts(skill: Path) -> dict:
    found = []
    for pat in ('__pycache__', '*.pyc', '*.pyo'):
        found.extend(str(p.relative_to(skill)) for p in skill.rglob(pat))
    return {'check': 'no_runtime_cache_artifacts', 'ok': not found, 'artifacts': sorted(set(found))[:100]}


def metadata(skill: Path, graph: dict) -> dict:
    ok = True
    details = {}
    canonical = [f"prompts/{item['prompt_file']}" for item in graph.get('phases', [])]
    optional = [
        f"prompts/{item['prompt_file']}"
        for item in graph.get('auxiliary_prompts', [])
    ]
    manifest = skill / 'manifest.json'
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text())
            details['manifest_name'] = data.get('name')
            details['manifest_sequence_matches_contract'] = (
                data.get('canonical_prompt_sequence') == canonical
                and data.get('optional_prompts') == optional
            )
            ok = ok and data.get('name') == 'zero-to-hero'
            ok = ok and details['manifest_sequence_matches_contract']
        except Exception as exc:
            ok = False
            details['manifest_error'] = str(exc)
    openai = skill / 'agents' / 'openai.yaml'
    if openai.exists():
        txt = openai.read_text(errors='ignore')
        details['openai_yaml_present'] = True
        ok = ok and 'allow_implicit_invocation: false' in txt
    return {'check': 'metadata', 'ok': ok, 'details': details}


def yaml_parse(skill: Path) -> dict:
    if yaml is None:
        return {
            'check': 'yaml_parse',
            'ok': False,
            'error': 'PyYAML unavailable; use the pinned repository environment',
        }
    failures=[]
    for p in list(skill.rglob('*.yaml'))+list(skill.rglob('*.yml')):
        if any(part in {'.git','.codex','.omx','.artifacts','__pycache__'} for part in p.parts):
            continue
        try:
            yaml.safe_load(p.read_text(errors='ignore'))
        except Exception as exc:
            failures.append({'path': str(p.relative_to(skill)), 'error': str(exc)[:240]})
    return {'check': 'yaml_parse', 'ok': not failures, 'failures': failures[:100]}


def reference_smoke(skill: Path) -> dict:
    failures=[]
    link_re=re.compile(r'\[[^\]]+\]\(([^)]+)\)')
    roots=[skill/'README.md', skill/'QUICKSTART.md', skill/'SKILL.md']
    roots += list((skill/'references').glob('*.md')) if (skill/'references').exists() else []
    roots += list((skill/'prompts').glob('*.md')) if (skill/'prompts').exists() else []
    for p in roots:
        if not p.exists():
            continue
        for m in link_re.finditer(p.read_text(errors='ignore')):
            target=m.group(1).split('#',1)[0].strip()
            if not target or '://' in target or target.startswith(('mailto:','#')):
                continue
            if target.endswith(('.png','.jpg','.jpeg','.svg','.gif','.webp')):
                continue
            candidate=(p.parent/target).resolve()
            try:
                candidate.relative_to(skill)
            except Exception:
                continue
            if not candidate.exists():
                failures.append({'path': str(p.relative_to(skill)), 'target': target})
    return {'check': 'reference_smoke', 'ok': not failures, 'missing': failures[:100]}


def output_profiles(skill: Path) -> dict:
    profile_dir = skill / 'references' / 'output-profiles'
    profiles = sorted(p.name for p in profile_dir.glob('*.yaml')) if profile_dir.exists() else []
    required = {'web-app.yaml','api-service.yaml','cli-tool.yaml','mechanical-product.yaml','pcb-electronics.yaml','robotics-product.yaml','docs-first-product.yaml'}
    missing = sorted(required - set(profiles))
    return {'check': 'output_profiles', 'ok': not missing, 'profile_count': len(profiles), 'missing': missing}


def list_checks() -> dict:
    return {'quick': ['required files','prompt sequence','metadata','runtime artifact check'], 'deep': ['deep required files','yaml parse','reference smoke','output profiles'], 'target_smoke': 'Run individual scripts such as run_fixture_tests.py, toolchain_preflight.py, and external_context_inventory.py for executable target smoke checks.'}


def main() -> int:
    ap=argparse.ArgumentParser(description='Side-effect-free zero-to-hero skill pack check. Use focused scripts for executable fixture/toolchain smoke checks.')
    ap.add_argument('path', nargs='?', default='.')
    ap.add_argument('--deep', action='store_true')
    ap.add_argument('--target-smoke', action='store_true', help='Add guidance for target smoke checks; does not execute them.')
    ap.add_argument('--timeout', type=int, default=45, help='Accepted for CLI compatibility; no child checks are spawned.')
    ap.add_argument('--max-seconds', type=int, default=180, help='Accepted for CLI compatibility; no child checks are spawned.')
    ap.add_argument('--jsonl', action='store_true', help='Emit each check as JSONL plus final summary.')
    ap.add_argument('--summary', action='store_true', help='emit concise summary JSON instead of full check details')
    ap.add_argument('--system-timeout', action='store_true', help='Accepted for CLI compatibility; no child checks are spawned.')
    ap.add_argument('--list-checks', action='store_true')
    ap.add_argument('--stop-on-fail', action='store_true')
    args=ap.parse_args()
    if args.list_checks:
        print(json.dumps(list_checks(), indent=2))
        return 0
    skill=resolve_skill(args.path)
    start=time.time()
    checks=[]
    try:
        graph = load_graph(skill)
    except ContractError as exc:
        graph = {'phases': [], 'auxiliary_prompts': []}
        checks.append({'check': 'contract_graph', 'ok': False, 'error': str(exc)})
    else:
        checks.append({'check': 'contract_graph', 'ok': True})
    planned=[]
    planned.extend(exists_checks(skill, REQUIRED))
    planned.extend([prompt_inventory(skill, graph), metadata(skill, graph), no_runtime_artifacts(skill)])
    if args.deep:
        planned.extend(exists_checks(skill, DEEP_REQUIRED))
        planned.extend([yaml_parse(skill), reference_smoke(skill), output_profiles(skill)])
    if args.target_smoke:
        planned.append({'check': 'target_smoke_guidance', 'ok': True, 'message': 'Run run_fixture_tests.py, toolchain_preflight.py, external_context_inventory.py, and repo_safety_check.py directly for executable target smoke checks.'})
    for c in planned:
        checks.append(c)
        if args.jsonl:
            print(json.dumps({'event':'check_finished', **c}))
        if args.stop_on_fail and not c.get('ok'):
            break
    status='pass' if all(c.get('ok') for c in checks) else 'fail'
    report={'status':status,'mode':'deep' if args.deep else 'quick','skill_dir':str(skill),'side_effect_free':True,'duration_seconds':round(time.time()-start,3),'checks':checks}
    if args.jsonl:
        print(json.dumps({'event':'summary', **report}))
    elif args.summary:
        failed=[c.get('check') for c in checks if not c.get('ok')]
        summary={
            'status': status,
            'mode': report['mode'],
            'skill_dir': str(skill),
            'side_effect_free': True,
            'target_smoke': bool(args.target_smoke),
            'duration_seconds': report['duration_seconds'],
            'total_checks': len(checks),
            'failed_checks': failed,
        }
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(report, indent=2))
    return 0 if status=='pass' else 1

if __name__=='__main__':
    raise SystemExit(main())
