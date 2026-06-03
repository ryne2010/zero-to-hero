#!/usr/bin/env python3
from __future__ import annotations
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
skill = root if (root / 'SKILL.md').exists() else root / '.agents/skills/zero-to-hero'
removed = []
for d in list(skill.rglob('__pycache__')) + list(skill.rglob('.codex')):
    if d.is_dir():
        shutil.rmtree(d)
        removed.append(str(d.relative_to(skill)))
for pattern in ['*.pyc', '*.pyo', '.DS_Store']:
    for p in list(skill.rglob(pattern)):
        if p.is_file():
            p.unlink()
            removed.append(str(p.relative_to(skill)))
print(f'pruned {len(removed)} generated artifacts')
for item in removed[:200]:
    print(item)
if len(removed) > 200:
    print(f'... {len(removed)-200} more')
