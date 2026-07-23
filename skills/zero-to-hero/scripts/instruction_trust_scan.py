#!/usr/bin/env python3
"""Scan a target repo for instruction-trust and prompt-injection risk surfaces.

This script is intentionally conservative: it reports suspicious instruction-like
content but does not fail unless --fail-on-high is passed. It treats findings as
review cues, not proof of malicious intent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {'.git','node_modules','.venv','venv','dist','build','.next','coverage','target','vendor','.codex','.omx','.agents','.artifacts'}
TEXT_EXTS = {'.md','.txt','.rst','.yaml','.yml','.json','.toml','.ini','.env','.example','.py','.js','.ts','.tsx','.jsx','.html','.css'}
ALLOW_PATH_PARTS = {'instruction-trust-policy.md','instruction_trust_scan.py','prompt-sequence-contract.md'}
PATTERNS = {
    'override_instructions': re.compile(r'\b(ignore|override|disregard) (all )?(previous|prior|system|developer|agent) instructions\b', re.I),
    'hide_from_user': re.compile(r'\b(do not tell|hide this|keep this secret from) (the )?user\b', re.I),
    'disable_safety': re.compile(r'\b(disable|bypass|turn off) (tests|checks|lint|safety|sandbox|approval|guardrails?)\b', re.I),
    'secret_access': re.compile(r'\b(read|print|exfiltrate|send|upload|leak) (.*)?(secret|token|api key|private key|\.env)\b', re.I),
    'destructive_command': re.compile(r'\b(rm -rf|sudo rm|delete all|wipe the repo|format disk)\b', re.I),
    'live_effects': re.compile(r'\b(enable|turn on|use) (live|production|real) (payments|email|sms|calls|providers|credentials)\b', re.I),
}

def should_scan(path: Path, root: Path) -> bool:
    if not path.is_file():
        return False
    rel = path.relative_to(root)
    if any(part in SKIP_DIRS for part in rel.parts):
        return False
    if any(part in ALLOW_PATH_PARTS for part in rel.parts):
        return False
    if path.suffix.lower() in TEXT_EXTS:
        return True
    if path.name in {'AGENTS.md','CODEX.md','FINAL_HANDOFF.md','README.md','.env.example'}:
        return True
    return False

def _redact_snippet(snippet: str) -> str:
    # Do not echo untrusted instruction text back into Codex context by default.
    # Raw snippets can be emitted only with --include-snippets for deliberate human review.
    return f'[redacted suspicious instruction-like text; chars={len(snippet)}]'


def scan(repo: Path, max_files: int = 5000, max_bytes: int = 1_000_000, include_snippets: bool = False) -> dict:
    findings=[]
    scanned_files = 0
    skipped_large = 0
    truncated = False
    for path in repo.rglob('*'):
        if not should_scan(path, repo):
            continue
        if scanned_files >= max_files:
            truncated = True
            break
        try:
            size = path.stat().st_size
        except Exception:
            size = 0
        if size > max_bytes:
            skipped_large += 1
            continue
        try:
            text = path.read_text(errors='ignore')
        except Exception:
            continue
        scanned_files += 1
        for name, pat in PATTERNS.items():
            for m in pat.finditer(text):
                line = text.count('\n', 0, m.start()) + 1
                snippet = text[max(0,m.start()-80):m.end()+80].replace('\n',' ')[:220]
                finding = {
                    'path': str(path.relative_to(repo)),
                    'line': line,
                    'risk': name,
                    'snippet_redacted': _redact_snippet(snippet),
                    'snippet_sha256': hashlib.sha256(snippet.encode('utf-8', errors='ignore')).hexdigest(),
                }
                if include_snippets:
                    finding['snippet'] = snippet
                findings.append(finding)
    severity = 'none'
    if findings:
        high = {'secret_access','destructive_command','disable_safety','live_effects'}
        severity = 'high' if any(f['risk'] in high for f in findings) else 'medium'
    return {'repo': str(repo), 'finding_count': len(findings), 'severity': severity, 'scanned_files': scanned_files, 'skipped_large_files': skipped_large, 'truncated': truncated, 'findings': findings[:500]}

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('repo', nargs='?', default='.')
    ap.add_argument('--fail-on-high', action='store_true')
    ap.add_argument('--max-files', type=int, default=5000)
    ap.add_argument('--max-bytes', type=int, default=1_000_000)
    ap.add_argument('--include-snippets', action='store_true', help='include raw suspicious snippets; default output redacts them to avoid re-injecting untrusted instructions into agent context')
    args=ap.parse_args()
    report=scan(Path(args.repo).resolve(), max_files=args.max_files, max_bytes=args.max_bytes, include_snippets=args.include_snippets)
    print(json.dumps(report, indent=2))
    if args.fail_on_high and report['severity']=='high':
        sys.exit(1)
