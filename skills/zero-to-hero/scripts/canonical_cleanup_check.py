#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys
from pathlib import Path

PATTERNS = {
    'iteration_noise': re.compile(r'\b(old lane|rejected direction|not approved|sample-only|approval-gated)\b', re.I),
    'placeholder_noise': re.compile(r'\b(TODO|FIXME|placeholder|stub|lorem ipsum|coming soon|example dashboard|tanstack start app)\b', re.I),
    'cleanup_noise': re.compile(r'\b(raw_spec|lossless_cleanup|preserved_yaml_text)\b', re.I),
}
SKIP_DIRS = {'.git', 'node_modules', '.venv', 'dist', 'build', '.next', 'coverage'}
EXTS = {'.md', '.txt', '.yaml', '.yml', '.json', '.ts', '.tsx', '.js', '.jsx', '.py', '.css'}
ALLOW_PATH_PARTS = {'changelog', 'changes', 'migrations'}
SKILL_INTERNAL_ALLOWLIST = {
    'scripts/canonical_cleanup_check.py',
    'references/canonical-cleanup-policy.md',
    'references/cleanup-allowlist.md',
    'prompts/09-canonical-cleanup.md',
}


def is_zero_to_hero_skill_root(repo: Path) -> bool:
    return (repo / 'SKILL.md').exists() and 'name: zero-to-hero' in (repo / 'SKILL.md').read_text(errors='ignore')


def should_scan(p: Path, repo: Path) -> bool:
    if not p.is_file() or p.suffix.lower() not in EXTS:
        return False
    rel = p.relative_to(repo)
    rels = str(rel)
    parts = rel.parts
    if any(part in SKIP_DIRS for part in parts):
        return False
    if any(part in rels.lower() for part in ALLOW_PATH_PARTS):
        return False
    # When validating the zero-to-hero skill itself, ignore intentional test fixtures and
    # the cleanup policy/check files that necessarily contain the banned terms as data.
    if is_zero_to_hero_skill_root(repo):
        if parts and parts[0] == 'fixtures':
            return False
        if rels in SKILL_INTERNAL_ALLOWLIST:
            return False
    # When validating a target repo that contains this skill, do not scan the skill internals.
    if len(parts) >= 3 and parts[0:3] == ('.agents', 'skills', 'zero-to-hero'):
        return False
    return True


def scan(repo: Path):
    findings = []
    for p in repo.rglob('*'):
        if not should_scan(p, repo):
            continue
        text = p.read_text(errors='ignore')
        for name, rx in PATTERNS.items():
            for m in rx.finditer(text):
                findings.append({'file': str(p.relative_to(repo)), 'kind': name, 'match': m.group(0)})
    return findings


if __name__ == '__main__':
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    findings = scan(repo)
    print(json.dumps({'count': len(findings), 'findings': findings[:200]}, indent=2))
    sys.exit(1 if findings else 0)
