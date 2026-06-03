#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {'.git','node_modules','.venv','venv','dist','build','.next','coverage','target','vendor','.codex','.omx','.agents','.artifacts'}

PATTERNS = {
    'figma_mcp': ['.mcp/figma.json','mcp.json','.cursor/mcp.json'],
    'figma_code_connect': ['**/*.figma.ts','**/*.figma.tsx','**/code-connect/**','**/*.connect.ts','**/*.connect.tsx'],
    'storybook': ['.storybook/main.ts','.storybook/main.js','.storybook/preview.ts','.storybook/preview.js','**/*.stories.tsx','**/*.stories.ts','**/*.stories.jsx','**/*.stories.js'],
    'playwright': ['playwright.config.ts','playwright.config.js','playwright.config.mjs','tests/**/*.spec.ts','e2e/**/*.spec.ts'],
    'visual_regression': ['chromatic.config.json','**/__screenshots__/**','**/screenshots/**','**/*.snap.png'],
    'design_tokens': ['tokens.json','tokens/**/*.json','design-tokens/**/*.json','style-dictionary.config.*','tokens.config.*','**/tokens.studio.json'],
    'approved_visual_assets': ['docs/ui/visual-assets/**','docs/screens/**/target.*','**/visual-targets/**'],
    'mechanical_cad': ['**/*.step','**/*.stp','**/*.stl','**/*.scad','**/*.FCStd','**/cad/**'],
    'text_to_cad': ['**/text-to-cad/**','**/*text*cad*.md','**/*cad*prompt*.md'],
    'kicad': ['**/*.kicad_pro','**/*.kicad_sch','**/*.kicad_pcb'],
    'pcb_outputs': ['**/gerbers/**','**/fab/**','**/*BOM*.csv','**/*bom*.csv','**/*pos*.csv'],
    'firmware_robotics': ['platformio.ini','**/CMakeLists.txt','**/*.ino','**/*.urdf','**/urdf/**','**/ros2_ws/**'],
}

RECOMMENDATIONS = {
    'figma_mcp': 'If Figma MCP is authoritative, map selected frames into screen contracts and decision-ledger entries.',
    'figma_code_connect': 'Use Code Connect mappings to bind design components to real code components before UI generation.',
    'storybook': 'Use Storybook stories as the component evidence surface and add stories for canonical states.',
    'playwright': 'Use Playwright to produce route screenshots, traces, and golden-flow evidence.',
    'visual_regression': 'Treat screenshot baselines as review evidence, not product policy unless approved.',
    'design_tokens': 'Normalize design tokens into the repo token contract before implementing UI polish.',
    'approved_visual_assets': 'Deconstruct visual assets into route/component/data/workflow contracts before implementation.',
    'mechanical_cad': 'Require dimensions, tolerances, manufacturing assumptions, and human engineering review before CAD use.',
    'text_to_cad': 'Use text-to-CAD prompts only after mechanical requirements and validation checks are documented.',
    'kicad': 'Use KiCad files with ERC/DRC/fabrication output checks and human electronics review.',
    'pcb_outputs': 'Treat fabrication outputs as generated evidence that must match the PCB source of truth.',
    'firmware_robotics': 'Tie firmware/robotics assets to bring-up plans, test evidence, and safety constraints.',
}


def in_skipped(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except Exception:
        return False
    return any(part in SKIP_DIRS for part in rel.parts)


def find_matches(root: Path, pattern: str) -> list[str]:
    if '**' in pattern or '*' in pattern:
        matches = [p for p in root.glob(pattern) if not in_skipped(p, root)]
    else:
        p = root / pattern
        matches = [p] if p.exists() and not in_skipped(p, root) else []
    out = []
    for p in matches[:50]:
        try:
            out.append(str(p.relative_to(root)))
        except Exception:
            out.append(str(p))
    return sorted(set(out))


def build_report(repo: Path) -> dict:
    findings = {}
    for category, patterns in PATTERNS.items():
        hits = []
        for pattern in patterns:
            hits.extend(find_matches(repo, pattern))
        if hits:
            findings[category] = sorted(set(hits))[:100]
    recommendations = [RECOMMENDATIONS[k] for k in sorted(findings) if k in RECOMMENDATIONS]
    context_count = sum(len(v) for v in findings.values())
    return {
        'tool': 'zero-to-hero-external-context-inventory',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'repo': str(repo),
        'context_categories': sorted(findings),
        'context_count': context_count,
        'findings': findings,
        'recommendations': recommendations,
        'authority_note': 'External context is evidence until accepted into the source-of-truth map and deconstructed into contracts.',
    }


def write_reports(repo: Path, report: dict) -> list[str]:
    outdir = repo / '.codex' / 'reports' / 'zero-to-hero'
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / 'external-context-inventory.json'
    md_path = outdir / 'external-context-inventory.md'
    json_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    lines = [
        '# External context inventory',
        '',
        f"Repo: `{report['repo']}`",
        '',
        'External context is evidence until accepted into the source-of-truth map and deconstructed into contracts.',
        '',
        '## Categories found',
    ]
    lines += [f'- {c}: {len(report["findings"].get(c, []))} file(s)' for c in report.get('context_categories', [])] or ['- none']
    lines += ['', '## Recommendations']
    lines += [f'- {r}' for r in report.get('recommendations', [])] or ['- none']
    lines += ['', '## Findings']
    for category, hits in report.get('findings', {}).items():
        lines.append(f'### {category}')
        lines += [f'- `{h}`' for h in hits[:30]]
        if len(hits) > 30:
            lines.append(f'- ... {len(hits) - 30} more')
        lines.append('')
    md_path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    return [str(json_path), str(md_path)]


def main() -> int:
    ap = argparse.ArgumentParser(description='Inventory external design, component, CAD, PCB, firmware, and verification context in a target repo.')
    ap.add_argument('repo', nargs='?', default='.', help='target repository root')
    ap.add_argument('--write', action='store_true', help='write reports under .codex/reports/zero-to-hero')
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    report = build_report(repo)
    if args.write:
        report['written_reports'] = write_reports(repo, report)
    print(json.dumps(report, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
