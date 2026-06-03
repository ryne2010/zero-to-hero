#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
try:
    import yaml
except Exception:
    print('PyYAML not installed; skipping YAML parse check safely')
    sys.exit(0)
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
fail=[]
for p in list(ROOT.rglob('*.yaml'))+list(ROOT.rglob('*.yml')):
    if '.git' in p.parts: continue
    try:
        yaml.safe_load(p.read_text(errors='ignore'))
    except Exception as e:
        fail.append((str(p.relative_to(ROOT)), str(e)))
if fail:
    print('YAML parse failures:')
    for f,e in fail[:200]: print(f'- {f}: {e}')
    sys.exit(1)
print('yaml parse check passed')
