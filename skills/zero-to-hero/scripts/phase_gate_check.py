#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
try:
    import yaml
except Exception:
    yaml = None

REQUIRED_PHASES = [
    'interview', 'research_and_capability_detection', 'canonical_docs_pack',
    'design_and_visual_pack', 'hardware_pack', 'harness_pack',
    'omx_handoff_pack', 'canonical_cleanup', 'implementation_readiness_review'
]

def main() -> int:
    skill = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    if not (skill / 'SKILL.md').exists():
        skill = skill / '.agents/skills/zero-to-hero'
    path = skill / 'references/phase-gates.yaml'
    if not path.exists():
        print('missing references/phase-gates.yaml')
        return 1
    if not yaml:
        print('PyYAML unavailable; phase gate file exists')
        return 0
    data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    gates = data.get('gates', {})
    missing = [p for p in REQUIRED_PHASES if p not in gates]
    if missing:
        print('missing phase gates:', ', '.join(missing))
        return 1
    print('phase gates: passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
