#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or '.').resolve()
    if (root / 'SKILL.md').exists():
        return root
    candidate = root / '.agents' / 'skills' / 'zero-to-hero'
    if (candidate / 'SKILL.md').exists():
        return candidate
    return root


def clean_runtime_artifacts(skill: Path) -> None:
    for cache in list(skill.rglob('__pycache__')):
        if cache.is_dir():
            shutil.rmtree(cache)
    for artifact in list(skill.rglob('*.pyc')) + list(skill.rglob('*.pyo')):
        if artifact.is_file():
            artifact.unlink()


def run_script(skill: Path, script_name: str, args: list[str] | None = None, timeout: int = 12) -> dict:
    args = args or []
    script = skill / 'scripts' / script_name
    if not script.exists():
        return {'ok': False, 'error': f'missing scripts/{script_name}'}
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    cmd = [sys.executable, str(script), *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': f'timeout after {timeout}s', 'cmd': cmd}
    return {
        'ok': result.returncode == 0,
        'returncode': result.returncode,
        'stdout_tail': result.stdout[-1200:],
        'stderr_tail': result.stderr[-1200:],
        'cmd': cmd,
    }


def list_checks() -> dict:
    return {
        'quick': [
            'required files',
            'prompt sequence',
            'phase gates',
            'pack validator',
            'runtime artifact check',
        ],
        'deep': [
            'fixture tests',
            'yaml parse',
            'reference check',
            'instruction-trust fixture scan',
        ],
        'target_smoke': [
            'toolchain preflight fixture',
            'external context fixture',
            'repo safety fixture',
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description='zero-to-hero skill health check. Fast and bounded by default; use --deep and --target-smoke explicitly for broader checks.'
    )
    parser.add_argument('path', nargs='?', default='.')
    parser.add_argument('--deep', action='store_true', help='run deterministic deeper self-checks')
    parser.add_argument('--target-smoke', action='store_true', help='include environment-sensitive fixture/toolchain smoke checks')
    parser.add_argument('--timeout', type=int, default=12, help='per-script timeout for child checks')
    parser.add_argument('--max-seconds', type=int, default=180, help='overall health-check time budget')
    parser.add_argument('--jsonl', action='store_true', help='emit per-check JSONL events plus final summary')
    parser.add_argument('--list-checks', action='store_true')
    parser.add_argument('--stop-on-fail', action='store_true')
    args = parser.parse_args()

    if args.list_checks:
        print(json.dumps(list_checks(), indent=2))
        return 0

    started = time.time()
    skill = resolve_skill(args.path)
    clean_runtime_artifacts(skill)
    checks: list[dict] = []

    def elapsed() -> float:
        return time.time() - started

    def budget_remaining() -> bool:
        return elapsed() < args.max_seconds

    def add(name: str, ok: bool, details=None) -> bool:
        check = {'check': name, 'ok': bool(ok), 'details': details or {}}
        checks.append(check)
        if args.jsonl:
            print(json.dumps({'event': 'check_finished', **check}))
        return bool(ok)

    required_paths = [
        'SKILL.md',
        'README.md',
        'QUICKSTART.md',
        'manifest.json',
        'skill-manifest.yaml',
        'agents/openai.yaml',
        'references/phase-state-machine.yaml',
        'references/output-profiles/web-app.yaml',
        'references/decision-ledger.md',
        'references/generated-file-manifest.md',
        'references/cleanup-allowlist.md',
        'references/first-run-checklist.md',
        'references/phase-gates.yaml',
        'references/risk-tiering.md',
        'references/source-research-policy.md',
        'references/target-repo-preflight.md',
        'references/repo-safety-preflight.md',
        'references/toolchain-preflight.md',
        'references/external-context-sources.md',
        'references/phase-prompt-contract.md',
        'references/acceptance-evidence.md',
        'references/final-handoff-quality-bar.md',
        'references/artifact-lifecycle.md',
        'references/instruction-trust-scan.md',
        'references/prompt-sequence-contract.md',
        'references/target-repo-audit-report.md',
        'references/prompt-bundle.md',
        'references/distribution.md',
        'references/operating-recipes.md',
        'references/proof-first-implementation.md',
        'references/final-stability-notes.md',
        'schemas/decision-ledger.schema.yaml',
        'schemas/generated-files-manifest.schema.yaml',
        'schemas/planning-evidence.schema.json',
        'schemas/recovery-task-graph.schema.yaml',
        'prompts/00-deep-interview.md',
        'prompts/10-implementation-readiness-review.md',
        'scripts/validate_zero_to_hero_pack.py',
        'scripts/run_fixture_tests.py',
        'scripts/zero_to_hero_check.py',
        'scripts/target_repo_audit.py',
        'scripts/repo_safety_check.py',
        'scripts/toolchain_preflight.py',
        'scripts/external_context_inventory.py',
        'scripts/phase_gate_check.py',
        'scripts/planning_evidence_check.py',
        'scripts/test_planning_evidence_check.py',
        'scripts/instruction_trust_scan.py',
        'scripts/prompt_sequence_check.py',
        'scripts/render_prompt_bundle.py',
        'scripts/build_skill_zip.py',
        'scripts/zero_to_hero_start.py',
    ]
    for rel in required_paths:
        ok = add(f'exists:{rel}', (skill / rel).exists())
        if args.stop_on_fail and not ok:
            break

    prompts = sorted((skill / 'prompts').glob('*.md')) if (skill / 'prompts').exists() else []
    prefixes: dict[str, list[str]] = {}
    for p in prompts:
        pref = p.name.split('-', 1)[0]
        prefixes.setdefault(pref, []).append(p.name)
    dupes = {k: v for k, v in prefixes.items() if k not in {'98', '99'} and len(v) > 1}
    add('no_duplicate_prompt_prefixes', not dupes, dupes)
    add('no_pycache', not list(skill.rglob('__pycache__')) and not list(skill.rglob('*.pyc')))
    add('no_redundant_reference_pairs', not any((skill / p).exists() for p in [
        'references/context-router.md',
        'references/skill-pack-health.md',
        'references/hardware-safety-and-review.md',
    ]))

    quick_scripts = [
        ('validate', 'validate_zero_to_hero_pack.py', [str(skill)]),
        ('prompt-sequence', 'prompt_sequence_check.py', [str(skill)]),
        ('phase-gates', 'phase_gate_check.py', [str(skill)]),
    ]
    deep_scripts = [
        ('fixture-tests', 'run_fixture_tests.py', [str(skill)]),
        ('yaml-parse', 'yaml_parse_check.py', [str(skill)]),
        ('reference-check', 'docs_reference_check.py', [str(skill)]),
        ('instruction-trust-fixture', 'instruction_trust_scan.py', [str(skill / 'fixtures' / 'prompt-injection-risk')]),
    ]
    target_smoke_scripts = [
        ('toolchain-preflight-fixture', 'toolchain_preflight.py', [str(skill / 'fixtures' / 'react-vite-scaffold')]),
        ('external-context-fixture', 'external_context_inventory.py', [str(skill / 'fixtures' / 'react-vite-scaffold')]),
        ('repo-safety-fixture', 'repo_safety_check.py', [str(skill / 'fixtures' / 'react-vite-scaffold')]),
    ]

    selected = quick_scripts + (deep_scripts if args.deep else []) + (target_smoke_scripts if args.target_smoke else [])
    for name, script, sargs in selected:
        if not budget_remaining():
            add(f'run:{name}', False, {'error': f'overall budget exceeded after {round(elapsed(), 3)}s', 'max_seconds': args.max_seconds})
            if args.stop_on_fail:
                break
            continue
        result = run_script(skill, script, sargs, timeout=args.timeout)
        ok = add(f'run:{name}', result.get('ok', False), result)
        if args.stop_on_fail and not ok:
            break

    status = 'pass' if all(c['ok'] for c in checks) else 'fail'
    report = {
        'status': status,
        'mode': 'deep' if args.deep else 'quick',
        'target_smoke': bool(args.target_smoke),
        'skill_dir': str(skill),
        'duration_seconds': round(time.time() - started, 3),
        'checks': checks,
    }
    if args.jsonl:
        print(json.dumps({'event': 'summary', **report}))
    else:
        print(json.dumps(report, indent=2))
    return 0 if status == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
