#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

TEXT_EXT = {'.md', '.yaml', '.yml', '.json', '.txt', '.gitignore'}

PROFILE_NAMES = {
    'auto','base','full','web-app','mobile-app','desktop-app','api-service','cli-tool',
    'ai-agent-app','data-ml-app','infra-repo','firmware-iot','mechanical-product',
    'pcb-electronics','robotics-product','docs-first-product'
}

CAPABILITY_TO_PROFILE = {
    'web_frontend': 'web-app',
    'mobile_app': 'mobile-app',
    'desktop_app': 'desktop-app',
    'api_backend': 'api-service',
    'cli_tool': 'cli-tool',
    'ai_agent_app': 'ai-agent-app',
    'data_ml_app': 'data-ml-app',
    'infra': 'infra-repo',
    'firmware': 'firmware-iot',
    'mechanical_cad': 'mechanical-product',
    'pcb_electronics': 'pcb-electronics',
    'robotics': 'robotics-product',
    'docs': 'docs-first-product',
}

BASE_PREFIXES = (
    'AGENTS.md','CODEX.md','FINAL_HANDOFF.md','README.md','.gitignore',
    '.codex/','.omx/','.artifacts/',
    'docs/00-meta/','docs/AGENT_CONTEXT.md','docs/implementation/',
)
PROFILE_PREFIXES = {
    'web-app': ('docs/ui/', '.agents/skills/frontend-parity/', 'docs/product-execution/', '.agents/skills/product-usability/', '.agents/skills/local-mode-verification/'),
    'mobile-app': ('docs/ui/', '.agents/skills/frontend-parity/', 'docs/product-execution/', '.agents/skills/product-usability/', '.agents/skills/local-mode-verification/'),
    'desktop-app': ('docs/ui/', '.agents/skills/frontend-parity/', 'docs/product-execution/', '.agents/skills/product-usability/', '.agents/skills/local-mode-verification/'),
    'api-service': ('docs/product-execution/', '.agents/skills/product-usability/', '.agents/skills/local-mode-verification/'),
    'cli-tool': ('docs/product-execution/', '.agents/skills/product-usability/', '.agents/skills/local-mode-verification/'),
    'ai-agent-app': ('docs/product-execution/', '.agents/skills/product-usability/', '.agents/skills/local-mode-verification/'),
    'data-ml-app': ('docs/product-execution/', '.agents/skills/product-usability/', '.agents/skills/local-mode-verification/'),
    'infra-repo': ('docs/product-execution/', '.agents/skills/local-mode-verification/'),
    'docs-first-product': ('docs/product-execution/', '.agents/skills/local-mode-verification/'),
    'firmware-iot': ('docs/hardware/', 'docs/firmware/', 'docs/product-execution/', '.agents/skills/local-mode-verification/'),
    'mechanical-product': ('docs/hardware/', 'docs/mechanical/', 'docs/product-execution/', '.agents/skills/local-mode-verification/'),
    'pcb-electronics': ('docs/hardware/', 'docs/pcb/', 'docs/product-execution/', '.agents/skills/local-mode-verification/'),
    'robotics-product': ('docs/hardware/', 'docs/firmware/', 'docs/mechanical/', 'docs/pcb/', 'docs/product-execution/', '.agents/skills/local-mode-verification/'),
}



def repo_safety(repo: Path) -> dict:
    env = os.environ.copy()
    env['GIT_OPTIONAL_LOCKS'] = '0'
    try:
        inside = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--is-inside-work-tree'], capture_output=True, text=True, timeout=8, env=env)
    except Exception as exc:
        return {'safe_to_write_templates': False, 'warnings': [f'git safety check unavailable: {exc}']}
    if inside.returncode != 0 or inside.stdout.strip() != 'true':
        return {'safe_to_write_templates': False, 'warnings': ['target is not inside a git work tree']}
    status = subprocess.run(['git', '-C', str(repo), 'status', '--porcelain=v1', '--untracked-files=all'], capture_output=True, text=True, timeout=8, env=env)
    branch = subprocess.run(['git', '-C', str(repo), 'branch', '--show-current'], capture_output=True, text=True, timeout=8, env=env)
    lines = [line for line in status.stdout.splitlines() if line.strip()] if status.returncode == 0 else []
    warnings = []
    if lines:
        warnings.append('target has uncommitted or untracked changes')
    if branch.stdout.strip() in {'main', 'master'}:
        warnings.append('target is on main/master; use a dedicated branch for generated artifacts')
    return {
        'safe_to_write_templates': not warnings,
        'branch': branch.stdout.strip() or None,
        'change_count': len(lines),
        'warnings': warnings,
    }

def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def detect_profiles(skill: Path, repo: Path) -> tuple[list[str], dict]:
    cap_script = skill / 'scripts' / 'capability_detect.py'
    if not cap_script.exists():
        return ['base'], {'capabilities': [], 'warning': 'capability_detect.py missing'}
    spec = importlib.util.spec_from_file_location('zero_to_hero_capability_detect', cap_script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    detection = module.detect(repo)
    profiles = ['base']
    for capability in detection.get('capabilities', []):
        profile = CAPABILITY_TO_PROFILE.get(capability)
        if profile and profile not in profiles:
            profiles.append(profile)
    if len(profiles) == 1:
        profiles.append('docs-first-product')
    return profiles, detection


def profile_set(skill: Path, repo: Path, profile_arg: str) -> tuple[list[str], dict]:
    if profile_arg not in PROFILE_NAMES:
        raise SystemExit(f'unknown profile {profile_arg!r}; use --list-profiles')
    if profile_arg == 'full':
        return ['full'], {'capabilities': ['full']}
    if profile_arg == 'auto':
        return detect_profiles(skill, repo)
    if profile_arg == 'base':
        return ['base'], {'capabilities': []}
    return ['base', profile_arg], {'capabilities': [profile_arg]}


def include_for_profiles(rel: Path, profiles: list[str]) -> bool:
    rels = rel.as_posix()
    if 'full' in profiles:
        return True
    if any(rels == p or rels.startswith(p) for p in BASE_PREFIXES):
        return True
    for profile in profiles:
        if any(rels == p or rels.startswith(p) for p in PROFILE_PREFIXES.get(profile, ())) :
            return True
    return False


def write_file(src: Path, dst: Path, force: bool, dry: bool) -> str:
    existed_before = dst.exists()
    if existed_before and not force:
        return 'skipped_exists'
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in TEXT_EXT or src.name in {'.gitignore'}:
            dst.write_text(read_text(src), encoding='utf-8')
        else:
            dst.write_bytes(src.read_bytes())
    if dry:
        return 'would_overwrite' if existed_before else 'would_create'
    return 'overwritten' if existed_before else 'created'


def apply_templates(skill: Path, repo: Path, dry: bool, force: bool, profile_arg: str, safety_report: dict | None = None) -> dict:
    templates = skill / 'templates'
    selected_profiles, detection = profile_set(skill, repo, profile_arg)
    manifest = {
        'tool': 'zero-to-hero',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'dry_run': dry,
        'force': force,
        'requested_profile': profile_arg,
        'selected_profiles': selected_profiles,
        'capability_detection': detection,
        'repo_safety': safety_report or {},
        'files_created': [],
        'files_modified': [],
        'files_skipped_existing': [],
        'files_skipped_profile': [],
        'files_not_touched': [
            {'path': 'src/', 'reason': 'zero-to-hero does not implement product runtime code'},
            {'path': 'app source files', 'reason': 'templates only create harness/docs/handoff artifacts'},
        ],
    }
    if not templates.exists():
        raise SystemExit(f'missing templates directory: {templates}')
    for src in sorted(templates.rglob('*')):
        if src.is_dir():
            continue
        rel = src.relative_to(templates)
        rec = {'path': str(rel), 'source': str(src.relative_to(skill))}
        if not include_for_profiles(rel, selected_profiles):
            manifest['files_skipped_profile'].append(rec | {'reason': f'not selected by profile(s): {selected_profiles}'})
            continue
        dst = repo / rel
        status = write_file(src, dst, force=force, dry=dry)
        if status == 'skipped_exists':
            manifest['files_skipped_existing'].append(rec | {'reason': 'target exists; use --force to overwrite intentionally'})
        elif status in {'overwritten', 'would_overwrite'}:
            manifest['files_modified'].append(rec | {'reason': 'force overwrite' if force else 'dry-run overwrite preview'})
        elif status in {'created', 'would_create'}:
            manifest['files_created'].append(rec)
        else:
            manifest['files_created'].append(rec | {'status': status})
    return manifest


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Apply zero-to-hero templates to a target repo. Dry-run by default.')
    ap.add_argument('repo', nargs='?', default='.', help='target repository root')
    ap.add_argument('--write', action='store_true', help='actually write files')
    ap.add_argument('--force', action='store_true', help='overwrite existing template targets; use sparingly')
    ap.add_argument('--profile', default='auto', choices=sorted(PROFILE_NAMES), help='template profile to apply; auto detects capabilities')
    ap.add_argument('--list-profiles', action='store_true', help='list available template profiles and exit')
    ap.add_argument('--manifest', default='.codex/reports/zero-to-hero/generated-files.manifest.json', help='manifest path relative to target repo')
    ap.add_argument('--require-clean', action='store_true', help='refuse --write unless git status is clean and target is not main/master')
    args = ap.parse_args()
    if args.list_profiles:
        print(json.dumps({'profiles': sorted(PROFILE_NAMES), 'default': 'auto'}, indent=2))
        raise SystemExit(0)
    repo = Path(args.repo).resolve()
    skill = Path(__file__).resolve().parents[1]
    safety_report = repo_safety(repo)
    if args.write and args.require_clean and not safety_report.get('safe_to_write_templates'):
        raise SystemExit('refusing to write because repo safety check is not clean; run repo_safety_check.py for details or omit --require-clean')
    manifest = apply_templates(skill, repo, dry=not args.write, force=args.force, profile_arg=args.profile, safety_report=safety_report)
    if args.write:
        out = repo / args.manifest
        out.parent.mkdir(parents=True, exist_ok=True)
        manifest['written_manifest'] = str(out)
        out.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))
