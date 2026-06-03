#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

CANONICAL = [
    '00-deep-interview.md',
    '01-research-and-capability-detection.md',
    '02-canonical-docs-pack.md',
    '03-design-visual-pack.md',
    '04-hardware-mechanical-pcb-pack.md',
    '05-frontend-parity-system.md',
    '06-product-usability-contract.md',
    '07-local-product-done-harness.md',
    '08-omx-handoff.md',
    '09-canonical-cleanup.md',
    '10-implementation-readiness-review.md',
]
OPTIONAL = ['98-target-repo-preflight.md', '99-one-shot-small-product.md']
GROUPS = {
    'canonical': CANONICAL,
    'all': OPTIONAL[:1] + CANONICAL + OPTIONAL[1:],
    'preflight': ['98-target-repo-preflight.md'],
    'one-shot': ['99-one-shot-small-product.md'],
    'design': ['03-design-visual-pack.md', '05-frontend-parity-system.md'],
    'harness': ['06-product-usability-contract.md', '07-local-product-done-harness.md'],
    'handoff': ['08-omx-handoff.md', '09-canonical-cleanup.md', '10-implementation-readiness-review.md'],
}


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or '.').resolve()
    if (root / 'SKILL.md').exists():
        return root
    candidate = root / '.agents/skills/zero-to-hero'
    if (candidate / 'SKILL.md').exists():
        return candidate
    return root


def prompt_text(skill: Path, name: str) -> str:
    path = skill / 'prompts' / name
    if not path.exists():
        raise FileNotFoundError(f'missing prompt {name}')
    return path.read_text(encoding='utf-8')


def render(skill: Path, group: str, target_repo: str | None) -> tuple[str, dict]:
    names = GROUPS.get(group)
    if not names:
        raise SystemExit(f'unknown group {group!r}; choose one of {sorted(GROUPS)}')
    lines = [
        '# zero-to-hero prompt bundle',
        '',
        f'- generated_at: {datetime.now(timezone.utc).isoformat()}',
        f'- group: {group}',
        f'- skill_dir: `{skill}`',
    ]
    if target_repo:
        lines.append(f'- target_repo: `{Path(target_repo).resolve()}`')
    lines += ['', 'Use these prompts in order unless the user explicitly chooses a different zero-to-hero mode.', '']
    manifest = {'generated_at': datetime.now(timezone.utc).isoformat(), 'group': group, 'prompts': names, 'target_repo': str(Path(target_repo).resolve()) if target_repo else None}
    for i, name in enumerate(names, start=1):
        text = prompt_text(skill, name)
        title = name[:-3]
        lines += [f'## {i}. {title}', '', f'Path: `prompts/{name}`', '', '```txt', text.rstrip(), '```', '']
    return '\n'.join(lines), manifest


def main() -> int:
    ap = argparse.ArgumentParser(description='Render zero-to-hero prompts into a copy/paste bundle.')
    ap.add_argument('skill', nargs='?', default='.', help='skill root or repo containing .agents/skills/zero-to-hero')
    ap.add_argument('--group', default='canonical', choices=sorted(GROUPS), help='prompt group to render')
    ap.add_argument('--target-repo', default=None, help='optional target repo path, used in the bundle header')
    ap.add_argument('--write', action='store_true', help='write bundle into target repo .codex/reports/zero-to-hero')
    ap.add_argument('--out', default=None, help='explicit output file')
    args = ap.parse_args()
    skill = resolve_skill(args.skill)
    bundle, manifest = render(skill, args.group, args.target_repo)
    if args.write or args.out:
        if args.out:
            out = Path(args.out).resolve()
        elif args.target_repo:
            out = Path(args.target_repo).resolve() / '.codex/reports/zero-to-hero/prompt-bundle.md'
        else:
            out = skill / 'prompt-bundle.md'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(bundle + '\n', encoding='utf-8')
        manifest_path = out.with_suffix('.manifest.json')
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': 'written', 'bundle': str(out), 'manifest': str(manifest_path), 'prompt_count': len(manifest['prompts'])}, indent=2))
    else:
        print(bundle)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
