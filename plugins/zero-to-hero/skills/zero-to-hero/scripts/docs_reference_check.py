#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
missing=[]
for p in ROOT.rglob('*.md'):
    if '.git' in p.parts:
        continue
    text=p.read_text(errors='ignore')
    for m in re.finditer(r'\(([^)]+)\)', text):
        target=m.group(1).split('#')[0]
        if not target or '://' in target or target.startswith('mailto:') or target.startswith('#'):
            continue
        if target.endswith(('.png','.jpg','.jpeg','.svg','.gif','.webp')):
            pass
        candidate=(p.parent/target).resolve()
        try:
            candidate.relative_to(ROOT)
        except ValueError:
            continue
        if not candidate.exists():
            missing.append((str(p.relative_to(ROOT)), target))
if missing:
    print('missing markdown references:')
    for f,t in missing[:200]:
        print(f'- {f} -> {t}')
    sys.exit(1)
print('docs reference check passed')
