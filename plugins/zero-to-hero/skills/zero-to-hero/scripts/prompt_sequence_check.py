#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys
from pathlib import Path

EXPECTED = [
 '00-deep-interview.md','01-research-and-capability-detection.md','02-canonical-docs-pack.md','03-design-visual-pack.md','04-hardware-mechanical-pcb-pack.md','05-frontend-parity-system.md','06-product-usability-contract.md','07-local-product-done-harness.md','08-omx-handoff.md','09-canonical-cleanup.md','10-implementation-readiness-review.md','98-target-repo-preflight.md','99-one-shot-small-product.md'
]
NO_CODE_PHASES = {'00','01','02','03','04','05','06','07','08','09','10','98'}

def resolve(path: str|None) -> Path:
    root=Path(path or '.').resolve()
    if (root/'SKILL.md').exists(): return root
    return root/'.agents/skills/zero-to-hero'

skill=resolve(sys.argv[1] if len(sys.argv)>1 else None)
pdir=skill/'prompts'
errors=[]; warnings=[]
files=sorted(p.name for p in pdir.glob('*.md')) if pdir.exists() else []
for e in EXPECTED:
    if e not in files: errors.append(f'missing prompt {e}')
extra=[f for f in files if f not in EXPECTED and f!='README.md']
if extra: warnings.append(f'extra prompt files: {extra}')
prefixes={}
for f in files:
    m=re.match(r'^(\d+)-', f)
    if m: prefixes.setdefault(m.group(1),[]).append(f)
for pref,names in prefixes.items():
    if pref!='99' and len(names)>1: errors.append(f'duplicate phase prefix {pref}: {names}')
for f in files:
    pref=f.split('-',1)[0]
    text=(pdir/f).read_text(errors='ignore')
    lowered = text.lower()
    blocks_code = any(phrase in lowered for phrase in [
        'do not implement product runtime code',
        'do not write implementation code',
        'do not write code',
        'do not write app code',
        'do not write app implementation code',
        'do not implement product code',
        'do not generate app source files',
        'do not modify app source files',
        'do not change app source files',
    ])
    if pref in NO_CODE_PHASES and not blocks_code and f!='README.md':
        warnings.append(f'{f} should explicitly block product implementation code')
print(json.dumps({'status':'pass' if not errors else 'fail','prompt_count':len(files),'errors':errors,'warnings':warnings}, indent=2))
if errors: sys.exit(1)
