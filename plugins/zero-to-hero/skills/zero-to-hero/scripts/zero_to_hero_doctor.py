#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

REQUIRED = [
    'SKILL.md', 'README.md', 'QUICKSTART.md', 'manifest.json', 'skill-manifest.yaml',
    'prompts/00-deep-interview.md', 'prompts/01-research-and-capability-detection.md',
    'prompts/02-canonical-docs-pack.md', 'prompts/10-implementation-readiness-review.md',
    'references/phase-state-machine.yaml', 'references/phase-gates.yaml',
    'references/skill-health-check.md', 'references/check-operability.md',
    'scripts/zero_to_hero_check.py', 'scripts/validate_zero_to_hero_pack.py',
    'scripts/run_fixture_tests.py', 'scripts/target_repo_audit.py',
]
DEEP_REQUIRED = [
    'references/output-profiles/web-app.yaml', 'references/output-profiles/api-service.yaml',
    'references/output-profiles/pcb-electronics.yaml', 'references/output-profiles/firmware-iot.yaml',
    'references/generated-file-manifest.md', 'references/rollback-policy.md',
    'references/repo-safety-preflight.md', 'references/instruction-trust-scan.md',
    'schemas/generated-files-manifest.schema.yaml', 'schemas/recovery-task-graph.schema.yaml',
    'fixtures/react-vite-scaffold/package.json', 'fixtures/api-fastapi/pyproject.toml',
    'fixtures/hardware-kicad/project.kicad_pro', 'fixtures/prompt-injection-risk/README.md',
]


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or '.').resolve()
    if (root / 'SKILL.md').exists():
        return root
    candidate = root / '.agents' / 'skills' / 'zero-to-hero'
    if (candidate / 'SKILL.md').exists():
        return candidate
    return root


def check_exists(skill: Path, rels: list[str]) -> list[dict]:
    return [{'check': f'exists:{rel}', 'ok': (skill / rel).exists()} for rel in rels]


def prompt_inventory(skill: Path) -> dict:
    prompts = sorted((skill / 'prompts').glob('*.md')) if (skill / 'prompts').exists() else []
    names = [p.name for p in prompts]
    prefixes: dict[str, list[str]] = {}
    for name in names:
        prefixes.setdefault(name.split('-', 1)[0], []).append(name)
    dupes = {k: v for k, v in prefixes.items() if k not in {'98', '99'} and len(v) > 1}
    return {'check': 'prompt_inventory', 'ok': len(prompts) >= 10 and not dupes, 'prompt_count': len(prompts), 'duplicates': dupes, 'prompts': names}


def runtime_artifacts(skill: Path) -> dict:
    artifacts = []
    for pat in ('__pycache__', '*.pyc', '*.pyo'):
        artifacts.extend(str(p.relative_to(skill)) for p in skill.rglob(pat))
    artifacts = sorted(set(artifacts))
    return {'check': 'no_runtime_cache_artifacts', 'ok': not artifacts, 'artifacts': artifacts[:50]}


def yaml_parse(skill: Path) -> dict:
    if yaml is None:
        return {
            'check': 'yaml_parse',
            'ok': False,
            'error': 'PyYAML unavailable; use the pinned repository environment',
        }
    failures = []
    for p in list(skill.rglob('*.yaml')) + list(skill.rglob('*.yml')):
        if any(part in {'.git', '.codex', '.omx', '.artifacts', '__pycache__'} for part in p.parts):
            continue
        try:
            yaml.safe_load(p.read_text(errors='ignore'))
        except Exception as exc:
            failures.append({'path': str(p.relative_to(skill)), 'error': str(exc)[:240]})
    return {'check': 'yaml_parse', 'ok': not failures, 'failures': failures[:100]}


def reference_smoke(skill: Path) -> dict:
    # Lightweight markdown reference smoke check. It intentionally avoids a full
    # exhaustive crawl so the doctor remains fast and side-effect free.
    failures = []
    md_files = list(skill.glob('*.md')) + list((skill / 'references').glob('*.md')) + list((skill / 'prompts').glob('*.md'))
    link_re = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
    for p in md_files:
        text = p.read_text(errors='ignore')
        for match in link_re.finditer(text):
            target = match.group(1).split('#', 1)[0].strip()
            if not target or '://' in target or target.startswith(('mailto:', '#')):
                continue
            if target.endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp')):
                continue
            candidate = (p.parent / target).resolve()
            try:
                candidate.relative_to(skill)
            except Exception:
                continue
            if not candidate.exists():
                failures.append({'path': str(p.relative_to(skill)), 'target': target})
    return {'check': 'reference_smoke', 'ok': not failures, 'missing': failures[:100]}


def metadata(skill: Path) -> dict:
    result = {'check': 'metadata', 'ok': True, 'details': {}}
    manifest = skill / 'manifest.json'
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text())
            result['details']['manifest_name'] = data.get('name')
            if data.get('name') != 'zero-to-hero':
                result['ok'] = False
                result['details']['manifest_error'] = 'manifest name should be zero-to-hero'
        except Exception as exc:
            result['ok'] = False
            result['details']['manifest_error'] = str(exc)
    openai = skill / 'agents' / 'openai.yaml'
    if openai.exists():
        txt = openai.read_text(errors='ignore')
        result['details']['openai_yaml_present'] = True
        if 'allow_implicit_invocation: false' not in txt:
            result['ok'] = False
            result['details']['openai_policy_error'] = 'allow_implicit_invocation should be false for broad repo-mutating skill'
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description='Fast, side-effect-free zero-to-hero operational doctor.')
    parser.add_argument('root', nargs='?', default='.', help='Skill root or repo root containing .agents/skills/zero-to-hero')
    parser.add_argument('--deep', action='store_true', help='Run deeper structural checks without spawning child checks.')
    parser.add_argument('--target-smoke', action='store_true', help='Report target-smoke guidance; use zero_to_hero_check.py for executable target smoke checks.')
    parser.add_argument('--timeout', type=int, default=30, help='Accepted for CLI compatibility; doctor does not spawn bounded child checks.')
    parser.add_argument('--max-seconds', type=int, default=120, help='Accepted for CLI compatibility; doctor does not spawn bounded child checks.')
    parser.add_argument('--json', action='store_true', help='Emit JSON report.')
    args = parser.parse_args()

    skill = resolve_skill(args.root)
    checks = []
    checks.extend(check_exists(skill, REQUIRED))
    checks.append(prompt_inventory(skill))
    checks.append(runtime_artifacts(skill))
    checks.append(metadata(skill))
    if args.deep:
        checks.extend(check_exists(skill, DEEP_REQUIRED))
        checks.append(yaml_parse(skill))
        checks.append(reference_smoke(skill))
    if args.target_smoke:
        checks.append({
            'check': 'target_smoke_guidance',
            'ok': True,
            'message': 'Doctor is side-effect-free. Run scripts/zero_to_hero_check.py --deep --target-smoke for executable target smoke checks.',
        })

    failures = [c for c in checks if not c.get('ok')]
    report = {
        'status': 'pass' if not failures else 'fail',
        'mode': 'deep' if args.deep else 'quick',
        'skill_dir': str(skill),
        'side_effect_free': True,
        'failures': failures,
        'checks': checks,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print('zero-to-hero doctor')
        print(f'skill_dir: {skill}')
        print(f'mode: {report["mode"]}')
        for check in checks:
            print(f'- {check["check"]}: {"ok" if check.get("ok") else "fail"}')
        if args.target_smoke:
            print('target-smoke note: run zero_to_hero_check.py --deep --target-smoke for executable smoke checks.')
        print('Doctor passed' if not failures else 'Doctor failed')
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
