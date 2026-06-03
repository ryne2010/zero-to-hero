#!/usr/bin/env python3
"""Build a deterministic zero-to-hero plugin/repo release archive."""
from __future__ import annotations

import argparse
import filecmp
import hashlib
import json
import os
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = REPO_ROOT / "plugins" / "zero-to-hero" / ".codex-plugin" / "plugin.json"

DEFAULT_INCLUDE_PATHS = [
    "skills",
    "plugins",
    "docs",
    "scripts",
    "tests",
    ".github",
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "Makefile",
    "pyproject.toml",
    ".agents/plugins/marketplace.json",
    ".gitattributes",
]

EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".codex"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_NAMES = {".DS_Store"}


def package_version() -> str:
    data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        raise SystemExit("plugins/zero-to-hero/.codex-plugin/plugin.json missing version")
    return version.strip()


def should_exclude(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT)
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return True
    if path.name in EXCLUDED_NAMES:
        return True
    if path.suffix in EXCLUDED_SUFFIXES:
        return True
    return False


def iter_files(include_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in include_paths:
        path = REPO_ROOT / item
        if not path.exists():
            raise SystemExit(f"archive include path missing: {item}")
        if path.is_file():
            if not should_exclude(path):
                files.append(path)
            continue
        for child in path.rglob("*"):
            if child.is_file() and not should_exclude(child):
                files.append(child)
    return sorted(set(files), key=lambda p: p.relative_to(REPO_ROOT).as_posix())


def write_zip(output: Path, files: list[Path]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            rel = path.relative_to(REPO_ROOT).as_posix()
            info = zipfile.ZipInfo(rel)
            # Stable timestamp for deterministic archives accepted by Python zipfile.
            info.date_time = (2024, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if os.access(path, os.X_OK) else 0o644) << 16
            zf.writestr(info, path.read_bytes())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_manifest_entries(files: list[Path]) -> list[dict[str, str | int]]:
    entries: list[dict[str, str | int]] = []
    for path in files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        entries.append({
            "path": rel,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return entries


def write_release_sidecars(output: Path, files: list[Path], version: str) -> dict[str, str | int]:
    digest = sha256_file(output)
    sha_path = output.with_suffix(output.suffix + ".sha256")
    sha_path.write_text(f"{digest}  {output.name}\n", encoding="utf-8")

    file_entries = file_manifest_entries(files)
    manifest_path = output.with_suffix(output.suffix + ".manifest.json")
    manifest = {
        "name": "zero-to-hero",
        "version": version,
        "archive": output.name,
        "archive_sha256": digest,
        "file_count": len(files),
        "deterministic_zip_timestamp": "2024-01-01T00:00:00",
        "included_paths": [entry["path"] for entry in file_entries],
        "files": file_entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "archive_sha256": digest,
        "sha256_file": str(sha_path.relative_to(REPO_ROOT)) if sha_path.is_relative_to(REPO_ROOT) else str(sha_path),
        "manifest_file": str(manifest_path.relative_to(REPO_ROOT)) if manifest_path.is_relative_to(REPO_ROOT) else str(manifest_path),
    }


def mirror_parity_errors() -> list[str]:
    source = REPO_ROOT / "skills" / "zero-to-hero"
    mirror = REPO_ROOT / "plugins" / "zero-to-hero" / "skills" / "zero-to-hero"
    ignored_parts = {"__pycache__"}
    ignored_suffixes = {".pyc", ".pyo"}

    def ignore(path: Path) -> bool:
        return any(part in ignored_parts for part in path.parts) or path.suffix in ignored_suffixes

    def files(root: Path) -> set[Path]:
        return {p.relative_to(root) for p in root.rglob("*") if p.is_file() and not ignore(p.relative_to(root))}

    if not source.exists():
        return ["missing source skill directory: skills/zero-to-hero"]
    if not mirror.exists():
        return ["missing plugin mirror skill directory: plugins/zero-to-hero/skills/zero-to-hero"]
    source_files = files(source)
    mirror_files = files(mirror)
    errors: list[str] = []
    for rel in sorted(source_files - mirror_files):
        errors.append(f"missing in plugin mirror: {rel.as_posix()}")
    for rel in sorted(mirror_files - source_files):
        errors.append(f"extra in plugin mirror: {rel.as_posix()}")
    for rel in sorted(source_files & mirror_files):
        if not filecmp.cmp(source / rel, mirror / rel, shallow=False):
            errors.append(f"different mirror file: {rel.as_posix()}")
    return errors


def validate_archive(path: Path) -> None:
    required = {
        "plugins/zero-to-hero/.codex-plugin/plugin.json",
        "plugins/zero-to-hero/skills/zero-to-hero/SKILL.md",
        "skills/zero-to-hero/SKILL.md",
        ".agents/plugins/marketplace.json",
        "README.md",
        "AGENTS.md",
        "LICENSE",
        ".gitattributes",
        "scripts/build_plugin_archive.py",
        "scripts/release_skill_workflow.py",
        "scripts/plugin_metadata_check.py",
        "tests/check_skill_mirror.py",
        "tests/smoke/run_skill_smoke.py",
        ".github/workflows/validate.yml",
    }
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        missing = sorted(required - names)
        forbidden = [name for name in names if "__pycache__" in name or name.endswith((".pyc", ".pyo")) or name.startswith(".codex/")]
        bad = zf.testzip()
    if missing:
        raise SystemExit("archive missing required files: " + ", ".join(missing))
    if forbidden:
        raise SystemExit("archive contains runtime/generated artifacts: " + ", ".join(forbidden[:10]))
    if bad:
        raise SystemExit(f"archive integrity failure at {bad}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Output zip path. Defaults to dist/zero-to-hero-<version>.zip")
    parser.add_argument("--include", action="append", help="Additional path to include, relative to repo root")
    parser.add_argument("--no-validate", action="store_true", help="Do not validate the completed archive")
    parser.add_argument("--no-sidecars", action="store_true", help="Do not write .sha256 and .manifest.json sidecar files")
    args = parser.parse_args()

    version = package_version()
    output = Path(args.output) if args.output else REPO_ROOT / "dist" / f"zero-to-hero-{version}.zip"
    if not output.is_absolute():
        output = REPO_ROOT / output
    include_paths = list(DEFAULT_INCLUDE_PATHS)
    if args.include:
        include_paths.extend(args.include)
    mirror_errors = mirror_parity_errors()
    if mirror_errors:
        raise SystemExit("source/plugin mirror parity failed before archive build:\n" + "\n".join(mirror_errors[:20]))
    files = iter_files(include_paths)
    write_zip(output, files)
    if not args.no_validate:
        validate_archive(output)
    sidecars = {} if args.no_sidecars else write_release_sidecars(output, files, version)
    rel = output.relative_to(REPO_ROOT) if output.is_relative_to(REPO_ROOT) else output
    payload = {"status": "pass", "archive": str(rel), "version": version, "file_count": len(files)}
    payload.update(sidecars)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
