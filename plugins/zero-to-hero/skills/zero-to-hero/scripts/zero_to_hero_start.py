#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True


def run_json(cmd: list[str], timeout_seconds: int = 60) -> dict:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors='ignore') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        stderr = exc.stderr.decode(errors='ignore') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
        return {
            'ok': False,
            'command': cmd,
            'error': f'timeout after {timeout_seconds}s',
            'stdout': stdout[-4000:],
            'stderr': stderr[-4000:],
        }
    if result.returncode != 0:
        return {
            'ok': False,
            'command': cmd,
            'returncode': result.returncode,
            'stdout': result.stdout[-4000:],
            'stderr': result.stderr[-4000:],
        }
    try:
        return json.loads(result.stdout)
    except Exception:
        return {'ok': True, 'command': cmd, 'stdout': result.stdout[-4000:], 'stderr': result.stderr[-4000:]}


def md_report(summary: dict) -> str:
    repo = summary.get('repo')
    profile = summary.get('profile')
    audit = summary.get('audit', {})
    templates = summary.get('template_preview', {})
    external = summary.get('external_context', {})
    caps = audit.get('capabilities', {}).get('capabilities', []) if isinstance(audit.get('capabilities'), dict) else []
    missing = audit.get('missing', [])
    recommended = audit.get('recommended_next_actions', [])
    lines = [
        '# zero-to-hero start report',
        '',
        f'Repo: `{repo}`',
        f'Profile: `{profile}`',
        f'Generated at: `{summary.get("generated_at")}`',
        '',
        '## Detected capabilities',
    ]
    lines += [f'- {cap}' for cap in caps] or ['- none detected']
    lines += ['', '## External context']
    categories = external.get('context_categories', []) if isinstance(external, dict) else []
    lines += [f'- {category}: {len(external.get("findings", {}).get(category, []))} file(s)' for category in categories] or ['- none detected']
    lines += ['', '## Repo safety']
    safety = summary.get('repo_safety', {})
    lines += [f"- safe to write templates without extra review: {str(safety.get('safe_to_write_templates')).lower()}"]
    for warning in safety.get('warnings', []):
        lines.append(f'- warning: {warning}')
    lines += ['', '## Missing readiness checks']
    lines += [f'- {m}' for m in missing] or ['- none']
    lines += ['', '## Recommended next actions']
    lines += [f'- {r}' for r in recommended] or ['- none']
    lines += ['', '## Template dry-run summary']
    lines += [
        f'- would create: {len(templates.get("files_created", []))}',
        f'- would modify: {len(templates.get("files_modified", []))}',
        f'- skipped existing: {len(templates.get("files_skipped_existing", []))}',
        f'- skipped by profile: {len(templates.get("files_skipped_profile", []))}',
    ]
    lines += ['', '## Suggested next prompt']
    lines += [
        'Use the zero-to-hero skill.',
        '',
        'Read the start report, target repo audit, and template dry-run manifest. Then run the appropriate next phase:',
        '',
        '- For unclear product scope: `prompts/00-deep-interview.md`',
        '- For existing repo preflight: `prompts/98-target-repo-preflight.md`',
        '- For docs/source-of-truth generation: `prompts/02-canonical-docs-pack.md`',
        '- For implementation-ready handoff: continue through the canonical prompt sequence.',
    ]
    lines += ['', '## Safety boundary']
    lines += [
        '- This start script does not implement product runtime code.',
        '- Template application is preview-only unless the user runs the template script with `--write`.',
        '- Review generated reports before applying templates or changing source files.',
    ]
    return '\n'.join(lines) + '\n'


def main() -> int:
    ap = argparse.ArgumentParser(description='Start a zero-to-hero run against a target repo. Writes only reports when --write is used.')
    ap.add_argument('repo', nargs='?', default='.', help='target repository root')
    ap.add_argument('--profile', default='auto', help='template profile for preview; default auto')
    ap.add_argument('--write', action='store_true', help='write .codex/reports/zero-to-hero/start-here.md and audit reports')
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    skill = Path(__file__).resolve().parents[1]
    reports_dir = repo / '.codex' / 'reports' / 'zero-to-hero'
    audit_cmd = [sys.executable, str(skill / 'scripts' / 'target_repo_audit.py'), str(repo)]
    if args.write:
        audit_cmd.append('--write')
    external_cmd = [sys.executable, str(skill / 'scripts' / 'external_context_inventory.py'), str(repo)]
    if args.write:
        external_cmd.append('--write')
    repo_safety_cmd = [sys.executable, str(skill / 'scripts' / 'repo_safety_check.py'), str(repo)]
    if args.write:
        repo_safety_cmd.append('--write')
    template_cmd = [
        sys.executable,
        str(skill / 'scripts' / 'apply_zero_to_hero_templates.py'),
        str(repo),
        '--profile',
        args.profile,
    ]
    audit = run_json(audit_cmd)
    external_context = run_json(external_cmd)
    repo_safety = run_json(repo_safety_cmd)
    templates = run_json(template_cmd)
    summary = {
        'tool': 'zero-to-hero-start',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'repo': str(repo),
        'profile': args.profile,
        'write': bool(args.write),
        'audit': audit,
        'external_context': external_context,
        'repo_safety': repo_safety,
        'template_preview': templates,
        'next_files_to_read': [
            'AGENTS.md',
            'CODEX.md',
            'FINAL_HANDOFF.md',
            '.codex/reports/zero-to-hero/target-repo-audit.md',
            '.codex/reports/zero-to-hero/external-context-inventory.md',
            '.codex/reports/zero-to-hero/repo-safety-check.md',
            '.codex/reports/zero-to-hero/start-here.md',
        ],
    }
    if args.write:
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / 'start-here.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        (reports_dir / 'start-here.md').write_text(md_report(summary), encoding='utf-8')
        summary['written_reports'] = [str(reports_dir / 'start-here.json'), str(reports_dir / 'start-here.md')]
    print(json.dumps(summary, indent=2))
    return 0 if audit.get('ok', True) is not False and external_context.get('ok', True) is not False and repo_safety.get('ok', True) is not False and templates.get('ok', True) is not False else 1


if __name__ == '__main__':
    raise SystemExit(main())
