#!/usr/bin/env python3
from __future__ import annotations
import sys, json, subprocess
from pathlib import Path

if __name__ == '__main__':
    repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
    skill=Path(__file__).resolve().parents[1]
    out=repo/'.omx/plans/zero-to-hero-plan.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    caps=json.loads(subprocess.check_output([sys.executable, str(skill/'scripts/capability_detect.py'), str(repo)]))
    cap_list=caps.get('capabilities', [])
    lines=['# zero-to-hero plan skeleton','', 'Detected capabilities:']
    lines += [f'- {c}' for c in cap_list] or ['- unknown']
    lines += ['', 'Recommended next steps:', '1. Run deep interview.', '2. Generate capability-aware docs pack.', '3. Generate harness pack.', '4. Create OMX single aggregate goal.', '5. Run canonical cleanup.', '']
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(str(out))
