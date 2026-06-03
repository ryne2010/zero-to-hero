#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True


def run_git(repo: Path, args: list[str], timeout: int = 8) -> tuple[int, str, str]:
    env = os.environ.copy()
    env['GIT_OPTIONAL_LOCKS'] = '0'
    try:
        result = subprocess.run(
            ['git', '-C', str(repo), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 127, '', 'git executable not found'
    except subprocess.TimeoutExpired:
        return 124, '', f'git command timed out after {timeout}s'


def status_porcelain(repo: Path) -> list[str]:
    code, out, _ = run_git(repo, ['status', '--porcelain=v1', '-uno'])
    if code != 0:
        return []
    return [line for line in out.splitlines() if line.strip()]


def untracked_porcelain(repo: Path) -> list[str]:
    code, out, _ = run_git(repo, ['status', '--porcelain=v1', '--untracked-files=all'])
    if code != 0:
        return []
    return [line for line in out.splitlines() if line.startswith('?? ')]


def build_report(repo: Path) -> dict:
    code, inside, err = run_git(repo, ['rev-parse', '--is-inside-work-tree'])
    is_git = code == 0 and inside == 'true'
    report = {
        'tool': 'zero-to-hero-repo-safety-check',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'repo': str(repo),
        'is_git_repo': is_git,
        'git_available': code != 127,
        'safe_to_write_templates': True,
        'warnings': [],
        'recommended_actions': [],
    }
    if not is_git:
        report['safe_to_write_templates'] = False
        report['warnings'].append('target is not inside a git work tree; changes cannot be reviewed or reverted through git')
        report['recommended_actions'].append('initialize git or create an archive/backup before writing generated files')
        if err:
            report['git_error'] = err
        return report

    _, branch, _ = run_git(repo, ['branch', '--show-current'])
    _, head, _ = run_git(repo, ['rev-parse', '--short', 'HEAD'])
    _, upstream, _ = run_git(repo, ['rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'])
    tracked_changes = status_porcelain(repo)
    untracked = untracked_porcelain(repo)
    report.update({
        'branch': branch or '(detached)',
        'head': head,
        'upstream': upstream or None,
        'tracked_change_count': len(tracked_changes),
        'untracked_file_count': len(untracked),
        'tracked_change_preview': tracked_changes[:40],
        'untracked_preview': untracked[:40],
        'has_uncommitted_changes': bool(tracked_changes),
        'has_untracked_files': bool(untracked),
    })
    if branch in {'main', 'master'}:
        report['warnings'].append('target is on main/master; generated files are safer on a dedicated branch')
        report['recommended_actions'].append('create a branch such as chore/zero-to-hero-handoff before writing')
    if tracked_changes:
        report['warnings'].append('target has tracked uncommitted changes')
        report['recommended_actions'].append('commit, stash, or intentionally acknowledge tracked changes before writing generated files')
    if untracked:
        report['warnings'].append('target has untracked files')
        report['recommended_actions'].append('review untracked files before writing generated files')
    if tracked_changes or untracked or branch in {'main', 'master'}:
        report['safe_to_write_templates'] = False
    if not report['recommended_actions']:
        report['recommended_actions'].append('safe to run zero-to-hero template dry-runs; review generated manifest before --write')
    return report


def md_report(report: dict) -> str:
    lines = ['# zero-to-hero repo safety check', '', f"Repo: `{report.get('repo')}`", '']
    lines += ['## Git status']
    if not report.get('is_git_repo'):
        lines += ['- git work tree: no']
    else:
        lines += [
            '- git work tree: yes',
            f"- branch: `{report.get('branch')}`",
            f"- head: `{report.get('head')}`",
            f"- tracked changes: {report.get('tracked_change_count', 0)}",
            f"- untracked files: {report.get('untracked_file_count', 0)}",
        ]
    lines += ['', '## Safety result', f"- safe to write templates without extra review: {str(report.get('safe_to_write_templates')).lower()}"]
    lines += ['', '## Warnings']
    lines += [f"- {w}" for w in report.get('warnings', [])] or ['- none']
    lines += ['', '## Recommended actions']
    lines += [f"- {a}" for a in report.get('recommended_actions', [])] or ['- none']
    if report.get('tracked_change_preview'):
        lines += ['', '## Tracked change preview']
        lines += [f"- `{x}`" for x in report.get('tracked_change_preview', [])]
    if report.get('untracked_preview'):
        lines += ['', '## Untracked file preview']
        lines += [f"- `{x}`" for x in report.get('untracked_preview', [])]
    return '\n'.join(lines) + '\n'


def main() -> int:
    ap = argparse.ArgumentParser(description='Check whether a target repo is safe for zero-to-hero generated file writes.')
    ap.add_argument('repo', nargs='?', default='.', help='target repository root')
    ap.add_argument('--write', action='store_true', help='write report files under .codex/reports/zero-to-hero')
    ap.add_argument('--fail-on-unsafe', action='store_true', help='exit nonzero when generated writes should be reviewed first')
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    report = build_report(repo)
    if args.write:
        outdir = repo / '.codex' / 'reports' / 'zero-to-hero'
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / 'repo-safety-check.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        (outdir / 'repo-safety-check.md').write_text(md_report(report), encoding='utf-8')
        report['written_reports'] = [str(outdir / 'repo-safety-check.json'), str(outdir / 'repo-safety-check.md')]
    print(json.dumps(report, indent=2))
    if args.fail_on_unsafe and not report.get('safe_to_write_templates'):
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
