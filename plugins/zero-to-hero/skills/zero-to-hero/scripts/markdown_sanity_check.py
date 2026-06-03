#!/usr/bin/env python3
from __future__ import annotations
import re
import sys
from pathlib import Path


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or '.').resolve()
    if (root / 'SKILL.md').exists():
        return root
    candidate = root / '.agents' / 'skills' / 'zero-to-hero'
    if (candidate / 'SKILL.md').exists():
        return candidate
    return root


def rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except Exception:
        return str(path)


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    in_fence = False
    opener = ''
    opener_line = 0
    fence_re = re.compile(r'^(?P<fence>`{3,}|~{3,})(?P<info>.*)$')
    for idx, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines(), start=1):
        stripped = line.strip()
        m = fence_re.match(stripped)
        if not m:
            continue
        fence = m.group('fence')
        info = m.group('info').strip()
        marker = fence[0]
        length = len(fence)
        if not in_fence:
            in_fence = True
            opener = marker * length
            opener_line = idx
        else:
            # A closing fence may be longer than the opener, but must not carry info text.
            if marker == opener[0] and length >= len(opener):
                if info:
                    errors.append(f'{path}:{idx}: closing fence has language/info text {info!r}; this usually means a nested fence was opened inside another fence')
                in_fence = False
                opener = ''
                opener_line = 0
            # Different fence marker inside a fence is allowed as literal content.
    if in_fence:
        errors.append(f'{path}:{opener_line}: unclosed fenced code block')
    return errors


def main() -> int:
    skill = resolve_skill(sys.argv[1] if len(sys.argv) > 1 else None)
    errors: list[str] = []
    for md in sorted(skill.rglob('*.md')):
        # Do not inspect generated fixture content outside the skill body; fixtures may intentionally include odd strings.
        if '/fixtures/' in str(md).replace('\\', '/'):
            continue
        errors.extend(check_file(md))
    if errors:
        print('markdown sanity check failed')
        for error in errors:
            print('ERROR:', error)
        return 1
    print('markdown sanity check passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
