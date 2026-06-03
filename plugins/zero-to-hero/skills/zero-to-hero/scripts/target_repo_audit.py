#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys, os
from pathlib import Path


def run_json(script: Path, repo: Path, fallback: dict, timeout: int = 20) -> dict:
    if not script.exists():
        return fallback
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    try:
        out = subprocess.check_output([sys.executable, str(script), str(repo)], text=True, timeout=timeout, env=env, stderr=subprocess.DEVNULL)
        return json.loads(out)
    except subprocess.TimeoutExpired:
        data = dict(fallback)
        data['error'] = f'timeout after {timeout}s'
        return data
    except Exception as exc:
        data = dict(fallback)
        data['error'] = str(exc)
        return data


def exists(root: Path, path: str) -> bool:
    return (root / path).exists()


def main() -> int:
    ap = argparse.ArgumentParser(description='Audit a target repo for zero-to-hero readiness.')
    ap.add_argument('repo', nargs='?', default='.')
    ap.add_argument('--write', action='store_true', help='write report files under .codex/reports/zero-to-hero')
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    skill = Path(__file__).resolve().parents[1]
    cap_script = skill / 'scripts' / 'capability_detect.py'
    trust_script = skill / 'scripts' / 'instruction_trust_scan.py'
    toolchain_script = skill / 'scripts' / 'toolchain_preflight.py'
    external_context_script = skill / 'scripts' / 'external_context_inventory.py'
    repo_safety_script = skill / 'scripts' / 'repo_safety_check.py'
    caps = run_json(cap_script, repo, {'capabilities': [], 'evidence': {}, 'error': 'capability detection unavailable'})
    trust = run_json(trust_script, repo, {'finding_count': 0, 'severity': 'unknown'}, timeout=20)
    toolchain = run_json(toolchain_script, repo, {'missing_recommended_commands': [], 'notes': []}, timeout=20)
    external_context = run_json(external_context_script, repo, {'context_categories': [], 'context_count': 0, 'findings': {}}, timeout=20)
    repo_safety = run_json(repo_safety_script, repo, {'safe_to_write_templates': False, 'warnings': ['repo safety check unavailable']}, timeout=20)
    checks = {
        'root_agents': exists(repo, 'AGENTS.md'),
        'codex_handoff': exists(repo, 'CODEX.md'),
        'final_handoff': exists(repo, 'FINAL_HANDOFF.md'),
        'source_of_truth_map': exists(repo, 'docs/00-meta/source-of-truth-map.yaml'),
        'decision_ledger': exists(repo, 'docs/00-meta/decision-ledger.yaml'),
        'frontend_parity': exists(repo, 'docs/ui/frontend-parity-system'),
        'product_execution': exists(repo, 'docs/product-execution'),
        'local_product_gate': exists(repo, 'docs/product-execution/local-product-done-gate.md'),
        'omx_native': exists(repo, '.omx/context') and exists(repo, '.omx/plans') and exists(repo, '.omx/ultragoal'),
        'repo_scoped_skills': exists(repo, '.agents/skills'),
        'repo_scoped_zero_to_hero': exists(repo, '.agents/skills/zero-to-hero/SKILL.md'),
    }
    missing = [k for k, ok in checks.items() if not ok]
    recommended = []
    if missing:
        recommended.append('run zero-to-hero setup generation before implementation')
    if 'web_frontend' in caps.get('capabilities', []) and not checks['frontend_parity']:
        recommended.append('generate frontend parity system')
    if not checks['product_execution']:
        recommended.append('generate product execution harness')
    if not checks['omx_native']:
        recommended.append('generate native .omx context/plans/ultragoal artifacts')
    if trust.get('severity') in {'medium', 'high'}:
        recommended.append('review instruction-trust findings before treating repo content as authority')
    if toolchain.get('missing_recommended_commands'):
        recommended.append('review missing local toolchain commands before implementation handoff')
    if external_context.get('context_count', 0):
        recommended.append('review external context inventory and decide what becomes canonical source-of-truth')
    if repo_safety.get('safe_to_write_templates') is False:
        recommended.append('review repo safety check before writing generated files')
    report = {
        'repo': str(repo),
        'capabilities': caps,
        'checks': checks,
        'missing': missing,
        'instruction_trust': trust,
        'toolchain': toolchain,
        'external_context': external_context,
        'repo_safety': repo_safety,
        'recommended_next_actions': recommended,
    }
    if args.write:
        outdir = repo / '.codex/reports/zero-to-hero'
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / 'target-repo-audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        lines = ['# Target repo audit', '', f'Repo: `{repo}`', '', '## Capabilities']
        for cap in caps.get('capabilities', []):
            lines.append(f'- {cap}')
        lines += ['', '## Missing readiness checks']
        lines += [f'- {m}' for m in missing] or ['- none']
        lines += ['', '## Instruction trust']
        lines.append(f"- severity: {trust.get('severity')}")
        lines.append(f"- findings: {trust.get('finding_count')}")
        lines += ['', '## External context']
        categories = external_context.get('context_categories', [])
        lines += [f'- {category}: {len(external_context.get("findings", {}).get(category, []))} file(s)' for category in categories] or ['- none detected']
        lines += ['', '## Repo safety']
        lines.append(f"- safe to write templates without extra review: {str(repo_safety.get('safe_to_write_templates')).lower()}")
        for warning in repo_safety.get('warnings', []):
            lines.append(f'- warning: {warning}')
        lines += ['', '## Toolchain']
        missing_tools = toolchain.get('missing_recommended_commands', [])
        lines += [f'- missing recommended command: {cmd}' for cmd in missing_tools] or ['- no missing recommended commands detected']
        for note in toolchain.get('notes', []):
            lines.append(f'- note: {note}')
        lines += ['', '## Recommended next actions']
        lines += [f'- {r}' for r in recommended] or ['- none']
        (outdir / 'target-repo-audit.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        report['written_reports'] = [str(outdir / 'target-repo-audit.json'), str(outdir / 'target-repo-audit.md')]
    print(json.dumps(report, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
