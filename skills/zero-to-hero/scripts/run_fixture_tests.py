#!/usr/bin/env python3
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or '.').resolve()
    if (root / 'SKILL.md').exists():
        return root
    candidate = root / '.agents' / 'skills' / 'zero-to-hero'
    if (candidate / 'SKILL.md').exists():
        return candidate
    return root


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def run_bounded(cmd: list[str], label: str, timeout: int, errors: list[str]) -> subprocess.CompletedProcess[str] | None:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            proc.kill()
        stdout, stderr = proc.communicate()
        tail = ((stdout or '') + (stderr or ''))[-500:]
        errors.append(f'{label} timed out after {timeout}s. Output tail: {tail}')
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description='Run zero-to-hero fixture tests. Deterministic and fast by default; toolchain smoke is opt-in.')
    parser.add_argument('path', nargs='?', default='.')
    parser.add_argument('--timeout', type=int, default=20, help='per-subprocess timeout seconds for optional smoke checks')
    parser.add_argument('--toolchain-smoke', action='store_true', help='also run the environment-dependent toolchain_preflight fixture smoke')
    parser.add_argument('--json', action='store_true', help='emit machine-readable JSON')
    args = parser.parse_args()

    skill = resolve_skill(args.path)
    errors: list[str] = []
    checks: list[dict] = []

    cap_path = skill / 'scripts/capability_detect.py'
    apply_path = skill / 'scripts/apply_zero_to_hero_templates.py'
    cap_module = load_module(cap_path, 'zero_to_hero_capability_detect') if cap_path.exists() else None
    apply_module = load_module(apply_path, 'zero_to_hero_apply_templates') if apply_path.exists() else None
    if cap_module is None:
        errors.append(f'missing {cap_path}')
    if apply_module is None:
        errors.append(f'missing {apply_path}')

    expect = {
        'idea-only': [],
        'react-vite-scaffold': ['web_frontend'],
        'nextjs-partial-app': ['web_frontend'],
        'api-fastapi': ['api_backend'],
        'cli-python': ['cli_tool'],
        'hardware-kicad': ['pcb_electronics'],
        'robotics-firmware': ['firmware'],
        'docs-first-product': ['docs_existing'],
        'messy-monorepo': ['web_frontend', 'monorepo'],
        'prompt-injection-risk': [],
    }

    if cap_module:
        for name, caps in expect.items():
            d = skill / 'fixtures' / name
            if not d.exists():
                errors.append(f'missing fixture {name}')
                checks.append({'check': f'fixture:{name}', 'ok': False, 'error': 'missing fixture'})
                continue
            data = cap_module.detect(d)
            found = set(data.get('capabilities', []))
            missing = [c for c in caps if c not in found]
            checks.append({'check': f'capability:{name}', 'ok': not missing, 'expected': caps, 'found': sorted(found), 'missing': missing})
            for c in missing:
                errors.append(f'{name}: expected {c}, got {sorted(found)}')

    def dry_apply(fixture: str) -> dict:
        if not apply_module:
            return {}
        try:
            return apply_module.apply_templates(
                skill=skill,
                repo=skill / 'fixtures' / fixture,
                dry=True,
                force=False,
                profile_arg='auto',
                safety_report={'safe_to_write_templates': False, 'warnings': ['fixture dry-run skips git safety subprocess']},
            )
        except Exception as exc:
            errors.append(f'apply dry-run failed for {fixture}: {exc}')
            checks.append({'check': f'apply:{fixture}', 'ok': False, 'error': str(exc)})
            return {}

    web_manifest = dry_apply('react-vite-scaffold')
    if web_manifest:
        checks.append({'check': 'apply:react-vite-scaffold', 'ok': True})
        created = {x['path'] for x in web_manifest.get('files_created', [])}
        skipped_profile = {x['path'] for x in web_manifest.get('files_skipped_profile', [])}
        ok = 'docs/ui/FRONTEND_CONTEXT.md' in created and 'docs/pcb/README.md' in skipped_profile
        checks.append({'check': 'profile:auto:web_app', 'ok': ok})
        if 'docs/ui/FRONTEND_CONTEXT.md' not in created:
            errors.append('profile auto for react-vite-scaffold should include docs/ui/FRONTEND_CONTEXT.md')
        if 'docs/pcb/README.md' not in skipped_profile:
            errors.append('profile auto for react-vite-scaffold should skip docs/pcb/README.md')

    pcb_manifest = dry_apply('hardware-kicad')
    if pcb_manifest:
        checks.append({'check': 'apply:hardware-kicad', 'ok': True})
        created = {x['path'] for x in pcb_manifest.get('files_created', [])}
        skipped_profile = {x['path'] for x in pcb_manifest.get('files_skipped_profile', [])}
        ok = 'docs/pcb/README.md' in created and 'docs/ui/FRONTEND_CONTEXT.md' in skipped_profile
        checks.append({'check': 'profile:auto:pcb', 'ok': ok})
        if 'docs/pcb/README.md' not in created:
            errors.append('profile auto for hardware-kicad should include docs/pcb/README.md')
        if 'docs/ui/FRONTEND_CONTEXT.md' not in skipped_profile:
            errors.append('profile auto for hardware-kicad should skip docs/ui/FRONTEND_CONTEXT.md')

    if args.toolchain_smoke:
        script = skill / 'scripts/toolchain_preflight.py'
        run = run_bounded([sys.executable, str(script), str(skill / 'fixtures' / 'react-vite-scaffold')], 'toolchain preflight smoke', timeout=args.timeout, errors=errors)
        if run is not None and run.returncode != 0:
            errors.append(f'toolchain preflight failed: {run.stderr or run.stdout}')
            checks.append({'check': 'toolchain_preflight_smoke', 'ok': False, 'returncode': run.returncode})
        elif run is not None:
            try:
                report = json.loads(run.stdout)
                ok = 'commands' in report and 'configs' in report
                checks.append({'check': 'toolchain_preflight_smoke', 'ok': ok})
                if not ok:
                    errors.append('toolchain preflight report missing commands/configs')
            except Exception as exc:
                errors.append(f'toolchain preflight emitted invalid JSON: {exc}')
                checks.append({'check': 'toolchain_preflight_smoke', 'ok': False, 'error': 'invalid_json'})

    if args.json:
        print(json.dumps({'status': 'fail' if errors else 'pass', 'checks': checks, 'errors': errors}, indent=2))
    else:
        print('fixture tests')
        if errors:
            for e in errors:
                print('ERROR:', e)
            return 1
        print('passed')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
