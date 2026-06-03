#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys, zipfile
from pathlib import Path

EXCLUDE_PARTS = {'__pycache__', '.git', '.pytest_cache', '.mypy_cache', '.codex'}
EXCLUDE_SUFFIXES = {'.pyc', '.pyo'}


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or '.').resolve()
    if (root / 'SKILL.md').exists():
        return root
    candidate = root / '.agents/skills/zero-to-hero'
    if (candidate / 'SKILL.md').exists():
        return candidate
    return root


def include(path: Path, skill: Path) -> bool:
    rel = path.relative_to(skill)
    if any(part in EXCLUDE_PARTS for part in rel.parts):
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description='Build a clean ZIP for the zero-to-hero skill directory.')
    ap.add_argument('skill', nargs='?', default='.', help='skill root or repo containing .agents/skills/zero-to-hero')
    ap.add_argument('--out', default='zero-to-hero-codex-skill-pack.zip')
    ap.add_argument('--skip-check', action='store_true')
    args = ap.parse_args()
    skill = resolve_skill(args.skill)
    if not (skill / 'SKILL.md').exists():
        raise SystemExit(f'could not locate skill root from {args.skill!r}')
    if not args.skip_check:
        check = skill / 'scripts' / 'zero_to_hero_check.py'
        if check.exists():
            run = subprocess.run([sys.executable, str(check), str(skill)], text=True)
            if run.returncode != 0:
                raise SystemExit(run.returncode)
    out = Path(args.out).resolve()
    if out.exists():
        out.unlink()
    prefix = Path('.agents/skills/zero-to-hero')
    count = 0
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(skill.rglob('*')):
            if path.is_dir() or not include(path, skill):
                continue
            zf.write(path, prefix / path.relative_to(skill))
            count += 1
    print(f'built {out} with {count} files')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
