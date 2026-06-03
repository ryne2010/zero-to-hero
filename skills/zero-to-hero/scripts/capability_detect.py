#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

FRONTEND_MARKERS = ['react', 'next', 'vite', 'tanstack', 'vue', 'nuxt', 'svelte', 'angular']
JS_API_MARKERS = ['express', 'fastify', 'hono', 'nestjs', 'trpc']
TEST_MARKERS = ['playwright', 'cypress', 'storybook', 'vitest', 'jest']
MOBILE_MARKERS = ['react-native', 'expo', 'flutter']
DESKTOP_MARKERS = ['electron', 'tauri']
AI_MARKERS = ['openai', 'langchain', 'llamaindex', 'litellm', 'anthropic', 'agents']
DB_MARKERS = ['prisma', 'drizzle', 'typeorm', 'sequelize', 'knex']
INFRA_MARKERS = ['terraform', 'pulumi', 'kubernetes', 'docker-compose']
PY_API_MARKERS = ['fastapi', 'django', 'flask']
PY_CLI_MARKERS = ['click', 'typer', 'argparse']
PY_AI_MARKERS = ['openai', 'langchain', 'llama-index', 'litellm', 'anthropic']
PY_DB_MARKERS = ['sqlalchemy', 'alembic', 'django']
SKIP_DIRS = {'.git','node_modules','.venv','venv','dist','build','.next','coverage','target','vendor','.codex','.omx','.agents','.artifacts'}


def _read(path: Path) -> str:
    try:
        return path.read_text(errors='ignore')
    except Exception:
        return ''


def detect(repo: str | Path) -> dict:
    root = Path(repo).resolve()
    capabilities: set[str] = set()
    evidence: dict[str, list[str]] = {}

    def add(cap: str, ev: str) -> None:
        capabilities.add(cap)
        evidence.setdefault(cap, []).append(ev)

    def exists(*parts: str) -> bool:
        return root.joinpath(*parts).exists()

    def in_skipped_dir(path: Path) -> bool:
        try:
            rel = path.relative_to(root)
        except Exception:
            return False
        return any(part in SKIP_DIRS for part in rel.parts)

    def glob(pattern: str):
        return [p for p in root.glob(pattern) if not in_skipped_dir(p)]

    pkg_files = []
    if (root / 'package.json').exists():
        pkg_files.append(root / 'package.json')
    pkg_files.extend(glob('**/package.json'))
    seen: set[Path] = set()
    for pf in pkg_files:
        if not pf.exists() or pf in seen:
            continue
        seen.add(pf)
        txt = _read(pf).lower()
        rel = str(pf.relative_to(root)) if pf != root else 'package.json'
        if any(x in txt for x in FRONTEND_MARKERS):
            add('web_frontend', f'{rel} frontend dependency')
        if any(x in txt for x in JS_API_MARKERS):
            add('api_backend', f'{rel} backend dependency')
        if any(x in txt for x in TEST_MARKERS):
            add('test_harness', f'{rel} test/dev dependency')
        if any(x in txt for x in MOBILE_MARKERS):
            add('mobile_app', f'{rel} mobile dependency')
        if any(x in txt for x in DESKTOP_MARKERS):
            add('desktop_app', f'{rel} desktop dependency')
        if any(x in txt for x in AI_MARKERS):
            add('ai_agent_app', f'{rel} AI/agent dependency')
        if any(x in txt for x in DB_MARKERS):
            add('database', f'{rel} database dependency')
        if 'workspaces' in txt or exists('pnpm-workspace.yaml'):
            add('monorepo', f'{rel} workspace config')

    if exists('src', 'routes') or glob('app/**/page.*') or glob('pages/**/*.tsx') or glob('src/**/*.tsx'):
        add('web_frontend', 'route/component-like files')

    py_files = [p for p in [root / 'pyproject.toml', root / 'requirements.txt'] if p.exists()]
    if py_files:
        txt = ' '.join(_read(p).lower() for p in py_files)
        if any(x in txt for x in PY_API_MARKERS):
            add('api_backend', 'python web framework dependency')
        if any(x in txt for x in PY_CLI_MARKERS):
            add('cli_tool', 'python CLI marker')
        if any(x in txt for x in PY_AI_MARKERS):
            add('ai_agent_app', 'python AI/agent dependency')
        if any(x in txt for x in PY_DB_MARKERS):
            add('database', 'python database dependency')

    if exists('Dockerfile') or exists('docker-compose.yml') or exists('compose.yml') or glob('**/*.tf') or exists('k8s') or exists('.github/workflows'):
        add('infra', 'infrastructure/deployment files')
    if exists('migrations') or glob('**/migrations/**'):
        add('database', 'migration files')
    if exists('ios') or exists('android'):
        add('mobile_app', 'native mobile directories')
    if exists('src-tauri'):
        add('desktop_app', 'Tauri project directory')
    if glob('**/*.kicad_pro') or glob('**/*.kicad_pcb'):
        add('pcb_electronics', 'KiCad project files')
    if glob('**/*.step') or glob('**/*.stl') or glob('**/*.scad'):
        add('mechanical_cad', 'mechanical CAD files')
    if glob('**/*.ino') or exists('platformio.ini') or glob('**/CMakeLists.txt'):
        add('firmware', 'firmware/build files')
    # Lightweight robotics hint. Keep capability low stakes; the output profile still requires user confirmation.
    if glob('**/urdf/**') or glob('**/*.urdf') or 'robot' in _read(root / 'README.md').lower():
        add('robotics', 'robotics marker in repo')
    if exists('docs'):
        add('docs_existing', 'docs directory')
    if exists('.omx'):
        add('omx', 'OMX directory')
    if exists('.agents', 'skills'):
        add('repo_scoped_skills', 'repo-scoped Codex skills')
    if not capabilities:
        add('unknown', 'no common stack markers found')
    return {'root': str(root), 'capabilities': sorted(capabilities), 'evidence': evidence}


if __name__ == '__main__':
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    print(json.dumps(detect(repo), indent=2))
