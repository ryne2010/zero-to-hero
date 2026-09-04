#!/usr/bin/env python3
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

COMMANDS = {
    'core': ['git', 'python3', 'node', 'npm'],
    'js_package_managers': ['pnpm', 'yarn', 'bun'],
    'containers': ['docker', 'docker-compose'],
    'task_runners': ['make', 'just'],
    'frontend_quality': ['npx'],
    'python': ['python', 'pip', 'pytest'],
    'go': ['go'],
    'rust': ['cargo', 'rustc'],
    'java': ['java', 'javac', 'gradle', 'mvn'],
    'mobile': ['flutter', 'xcodebuild', 'pod'],
    'hardware': ['kicad-cli', 'openscad', 'freecad', 'platformio'],
    'infra': ['terraform', 'kubectl', 'helm', 'gcloud', 'aws', 'az'],
}

CAPABILITY_RECOMMENDED = {
    'web_frontend': ['node', 'npm'],
    'mobile_app': ['node'],
    'desktop_app': ['node'],
    'api_backend': ['python3', 'docker'],
    'database': ['docker'],
    'infra': ['terraform'],
    'firmware': ['platformio'],
    'mechanical_cad': ['python3', 'npx'],
    'pcb_electronics': ['kicad-cli'],
    'robotics': ['python3', 'npx'],
}

KNOWN_CONFIGS = {
    'playwright': ['playwright.config.ts', 'playwright.config.js', 'playwright.config.mjs'],
    'storybook': ['.storybook/main.ts', '.storybook/main.js'],
    'figma_mcp': ['.mcp/figma.json', 'mcp.json', '.cursor/mcp.json'],
    'codex': ['AGENTS.md', 'CODEX.md', '.agents/skills'],
    'omx_neutral_handoff': [
        'docs/implementation/IMPLEMENTATION_BRIEF.md',
        'docs/implementation/EXECPLAN.md',
        'docs/implementation/PLANNING_EVIDENCE.md',
        'scripts/zero_to_hero_handoff_check.py',
    ],
    'docker': ['docker-compose.yml', 'compose.yml', 'Dockerfile'],
    'kicad': ['*.kicad_pro'],
}


def command_info(command: str) -> dict:
    path = shutil.which(command)
    return {'command': command, 'available': bool(path), 'path': path}


def detect_configs(repo: Path) -> dict:
    out: dict[str, list[str]] = {}
    for name, patterns in KNOWN_CONFIGS.items():
        matches: list[str] = []
        for pattern in patterns:
            if '*' in pattern:
                matches.extend(str(p.relative_to(repo)) for p in repo.glob(pattern))
            else:
                p = repo / pattern
                if p.exists():
                    matches.append(pattern)
        out[name] = sorted(set(matches))
    return out


def load_capabilities(repo: Path, skill: Path) -> list[str]:
    cap_script = skill / 'scripts' / 'capability_detect.py'
    if not cap_script.exists():
        return []
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('z2h_cap', cap_script)
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)
        return list(mod.detect(repo).get('capabilities', []))
    except Exception:
        return []


def build_report(repo: Path, skill: Path) -> dict:
    groups = {group: [command_info(c) for c in commands] for group, commands in COMMANDS.items()}
    available = {item['command'] for items in groups.values() for item in items if item['available']}
    capabilities = load_capabilities(repo, skill)
    recommended = sorted({cmd for cap in capabilities for cmd in CAPABILITY_RECOMMENDED.get(cap, [])})
    missing_recommended = [cmd for cmd in recommended if cmd not in available]
    configs = detect_configs(repo)
    notes = []
    if 'web_frontend' in capabilities and not configs.get('playwright'):
        notes.append('web_frontend detected but no Playwright config found; frontend parity evidence may require setup')
    if 'web_frontend' in capabilities and not configs.get('storybook'):
        notes.append('web_frontend detected but no Storybook config found; component evidence can still use app routes')
    if 'pcb_electronics' in capabilities and 'kicad-cli' not in available:
        notes.append('pcb_electronics detected but kicad-cli is unavailable; PCB checks may need manual/human review')
    if 'mechanical_cad' in capabilities and not {'python3', 'npx'} <= available:
        notes.append(
            'mechanical_cad detected but Python or npx is unavailable; '
            'the earthtojake/text-to-cad adapter cannot be probed'
        )
    return {
        'tool': 'zero-to-hero-toolchain-preflight',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'repo': str(repo),
        'capabilities': capabilities,
        'commands': groups,
        'configs': configs,
        'recommended_commands': recommended,
        'missing_recommended_commands': missing_recommended,
        'notes': notes,
    }


def write_reports(repo: Path, report: dict) -> list[str]:
    outdir = repo / '.codex' / 'reports' / 'zero-to-hero'
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / 'toolchain-preflight.json'
    md_path = outdir / 'toolchain-preflight.md'
    json_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    lines = [
        '# Toolchain preflight',
        '',
        f"Repo: `{report['repo']}`",
        '',
        '## Capabilities',
    ]
    lines += [f'- {cap}' for cap in report.get('capabilities', [])] or ['- none detected']
    lines += ['', '## Missing recommended commands']
    lines += [f'- {cmd}' for cmd in report.get('missing_recommended_commands', [])] or ['- none']
    lines += ['', '## Notes']
    lines += [f'- {note}' for note in report.get('notes', [])] or ['- none']
    lines += ['', '## Available command groups']
    for group, items in report.get('commands', {}).items():
        avail = [i['command'] for i in items if i.get('available')]
        lines.append(f'- {group}: {", ".join(avail) if avail else "none"}')
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return [str(json_path), str(md_path)]


def main() -> int:
    ap = argparse.ArgumentParser(description='Inspect local toolchain readiness for zero-to-hero target repo work.')
    ap.add_argument('repo', nargs='?', default='.', help='target repository root')
    ap.add_argument('--write', action='store_true', help='write report files under .codex/reports/zero-to-hero')
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    skill = Path(__file__).resolve().parents[1]
    report = build_report(repo, skill)
    if args.write:
        report['written_reports'] = write_reports(repo, report)
    print(json.dumps(report, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
