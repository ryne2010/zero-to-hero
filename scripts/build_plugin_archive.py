#!/usr/bin/env python3
"""Build a deterministic zero-to-hero plugin/repo release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path
from typing import Callable

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
    "uv.lock",
    ".agents/plugins/marketplace.json",
    ".gitattributes",
]

EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".codex"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_NAMES = {".DS_Store"}

# These repository entry points are intentionally executable in release archives.
# Skill-owned scripts are covered separately by their canonical directory shape.
EXECUTABLE_REPO_SCRIPTS = {
    "scripts/build_plugin_archive.py",
    "scripts/plugin_metadata_check.py",
    "scripts/validate_plugin_repo.py",
    "tests/smoke/run_all_smoke.py",
    "tests/smoke/run_plugin_archive_smoke.py",
}


def _repo_relative(path: Path) -> Path:
    """Return a normalized repository-relative path without resolving symlinks."""
    absolute = Path(os.path.abspath(path))
    try:
        return absolute.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise SystemExit(f"archive path escapes repository root: {path}") from exc


def _verified_repo_path(path: Path) -> tuple[Path, os.stat_result]:
    """Verify containment and reject symlinks in every path component."""
    rel = _repo_relative(path)
    current = REPO_ROOT
    try:
        for part in rel.parts:
            current = current / part
            current_stat = current.lstat()
            if stat.S_ISLNK(current_stat.st_mode):
                raise SystemExit(f"archive symlink is not allowed: {rel.as_posix()}")
        final_stat = current.lstat()
    except FileNotFoundError as exc:
        raise SystemExit(f"archive include path missing: {rel.as_posix()}") from exc

    try:
        current.resolve(strict=True).relative_to(REPO_ROOT)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"archive path escapes repository root: {rel.as_posix()}") from exc
    return rel, final_stat


def _read_repo_regular_file(path: Path) -> tuple[Path, bytes]:
    """Read a verified regular file without following a final symlink."""
    rel, path_stat = _verified_repo_path(path)
    if not stat.S_ISREG(path_stat.st_mode):
        raise SystemExit(f"archive entry is not a regular file: {rel.as_posix()}")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SystemExit(f"unable to safely open archive file: {rel.as_posix()}: {exc}") from exc
    try:
        opened_stat = os.fstat(descriptor)
        if not stat.S_ISREG(opened_stat.st_mode):
            raise SystemExit(f"archive entry is not a regular file: {rel.as_posix()}")
        _, current_stat = _verified_repo_path(path)
        if (opened_stat.st_dev, opened_stat.st_ino) != (current_stat.st_dev, current_stat.st_ino):
            raise SystemExit(f"archive file changed during safe open: {rel.as_posix()}")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            return rel, handle.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _walk_regular_files(root: Path, exclude: Callable[[Path], bool]) -> list[Path]:
    """Walk a repository directory without following or accepting symlinks."""
    rel, root_stat = _verified_repo_path(root)
    if stat.S_ISREG(root_stat.st_mode):
        return [] if exclude(root) else [root]
    if not stat.S_ISDIR(root_stat.st_mode):
        raise SystemExit(f"archive entry is not a regular file or directory: {rel.as_posix()}")

    files: list[Path] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name, reverse=True)
        except OSError as exc:
            raise SystemExit(
                f"unable to inspect archive directory: {_repo_relative(directory).as_posix()}: {exc}"
            ) from exc
        for entry in entries:
            child = Path(entry.path)
            child_rel, child_stat = _verified_repo_path(child)
            if exclude(child):
                continue
            if stat.S_ISDIR(child_stat.st_mode):
                pending.append(child)
            elif stat.S_ISREG(child_stat.st_mode):
                files.append(child)
            else:
                raise SystemExit(
                    f"archive entry is not a regular file or directory: {child_rel.as_posix()}"
                )
    return files


def package_version() -> str:
    _, payload = _read_repo_regular_file(PLUGIN_JSON)
    data = json.loads(payload.decode("utf-8"))
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
        files.extend(_walk_regular_files(path, should_exclude))
    return sorted(set(files), key=lambda p: p.relative_to(REPO_ROOT).as_posix())


def is_intended_executable(rel: Path) -> bool:
    """Return whether a canonical archive path is an intended executable."""
    posix = rel.as_posix()
    if posix in EXECUTABLE_REPO_SCRIPTS:
        return True
    parts = rel.parts
    source_skill_script = (
        len(parts) == 4
        and parts[:3] == ("skills", "zero-to-hero", "scripts")
        and rel.suffix == ".py"
    )
    plugin_skill_script = (
        len(parts) == 6
        and parts[:5] == ("plugins", "zero-to-hero", "skills", "zero-to-hero", "scripts")
        and rel.suffix == ".py"
    )
    return source_skill_script or plugin_skill_script


def canonical_zip_mode(rel: Path) -> int:
    """Return a host-independent permission mode for an archive path."""
    return 0o755 if is_intended_executable(rel) else 0o644


def write_zip(output: Path, files: list[Path]) -> None:
    entries: list[tuple[Path, bytes]] = []
    seen: set[Path] = set()
    for path in files:
        rel, data = _read_repo_regular_file(path)
        if rel in seen:
            raise SystemExit(f"duplicate archive path: {rel.as_posix()}")
        seen.add(rel)
        entries.append((rel, data))
    entries.sort(key=lambda entry: entry[0].as_posix())

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel, data in entries:
            info = zipfile.ZipInfo(rel.as_posix())
            # Stable timestamp for deterministic archives accepted by Python zipfile.
            info.date_time = (2024, 1, 1, 0, 0, 0)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | canonical_zip_mode(rel)) << 16
            zf.writestr(info, data)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_manifest_entries(files: list[Path]) -> list[dict[str, str | int]]:
    entries: list[dict[str, str | int]] = []
    for path in files:
        rel, data = _read_repo_regular_file(path)
        entries.append(
            {
                "path": rel.as_posix(),
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
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
        "sha256_file": str(sha_path.relative_to(REPO_ROOT))
        if sha_path.is_relative_to(REPO_ROOT)
        else str(sha_path),
        "manifest_file": str(manifest_path.relative_to(REPO_ROOT))
        if manifest_path.is_relative_to(REPO_ROOT)
        else str(manifest_path),
    }


def mirror_parity_errors() -> list[str]:
    source = REPO_ROOT / "skills" / "zero-to-hero"
    mirror = REPO_ROOT / "plugins" / "zero-to-hero" / "skills" / "zero-to-hero"
    ignored_parts = {"__pycache__"}
    ignored_suffixes = {".pyc", ".pyo"}

    def ignore(path: Path) -> bool:
        return any(part in ignored_parts for part in path.parts) or path.suffix in ignored_suffixes

    errors: list[str] = []
    try:
        source_files = {
            path.relative_to(source)
            for path in _walk_regular_files(source, lambda path: ignore(path.relative_to(source)))
        }
    except SystemExit as exc:
        errors.append(f"source skill archive safety failure: {exc}")
        source_files = set()
    try:
        mirror_files = {
            path.relative_to(mirror)
            for path in _walk_regular_files(mirror, lambda path: ignore(path.relative_to(mirror)))
        }
    except SystemExit as exc:
        errors.append(f"plugin mirror archive safety failure: {exc}")
        mirror_files = set()
    if errors:
        return errors
    for rel in sorted(source_files - mirror_files):
        errors.append(f"missing in plugin mirror: {rel.as_posix()}")
    for rel in sorted(mirror_files - source_files):
        errors.append(f"extra in plugin mirror: {rel.as_posix()}")
    for rel in sorted(source_files & mirror_files):
        _, source_data = _read_repo_regular_file(source / rel)
        _, mirror_data = _read_repo_regular_file(mirror / rel)
        if source_data != mirror_data:
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
        "uv.lock",
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
        forbidden = [
            name
            for name in names
            if "__pycache__" in name
            or name.endswith((".pyc", ".pyo"))
            or name.startswith(".codex/")
        ]
        metadata_errors: list[str] = []
        for info in zf.infolist():
            rel = Path(info.filename)
            if rel.is_absolute() or ".." in rel.parts or rel.as_posix() != info.filename:
                metadata_errors.append(f"non-canonical archive path: {info.filename}")
                continue
            unix_mode = info.external_attr >> 16
            expected_mode = canonical_zip_mode(rel)
            if info.create_system != 3:
                metadata_errors.append(f"non-Unix create_system: {info.filename}")
            if stat.S_IFMT(unix_mode) != stat.S_IFREG:
                metadata_errors.append(f"not marked as regular file: {info.filename}")
            if stat.S_IMODE(unix_mode) != expected_mode:
                metadata_errors.append(
                    f"non-canonical mode for {info.filename}: "
                    f"expected {oct(expected_mode)}, got {oct(stat.S_IMODE(unix_mode))}"
                )
            if info.date_time != (2024, 1, 1, 0, 0, 0):
                metadata_errors.append(f"non-canonical timestamp: {info.filename}")
        bad = zf.testzip()
    if missing:
        raise SystemExit("archive missing required files: " + ", ".join(missing))
    if forbidden:
        raise SystemExit(
            "archive contains runtime/generated artifacts: " + ", ".join(forbidden[:10])
        )
    if metadata_errors:
        raise SystemExit(
            "archive contains non-canonical metadata: " + "; ".join(metadata_errors[:10])
        )
    if bad:
        raise SystemExit(f"archive integrity failure at {bad}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", help="Output zip path. Defaults to dist/zero-to-hero-<version>.zip"
    )
    parser.add_argument(
        "--include", action="append", help="Additional path to include, relative to repo root"
    )
    parser.add_argument(
        "--no-validate", action="store_true", help="Do not validate the completed archive"
    )
    parser.add_argument(
        "--no-sidecars",
        action="store_true",
        help="Do not write .sha256 and .manifest.json sidecar files",
    )
    args = parser.parse_args()

    version = package_version()
    output = (
        Path(args.output) if args.output else REPO_ROOT / "dist" / f"zero-to-hero-{version}.zip"
    )
    if not output.is_absolute():
        output = REPO_ROOT / output
    include_paths = list(DEFAULT_INCLUDE_PATHS)
    if args.include:
        include_paths.extend(args.include)
    mirror_errors = mirror_parity_errors()
    if mirror_errors:
        raise SystemExit(
            "source/plugin mirror parity failed before archive build:\n"
            + "\n".join(mirror_errors[:20])
        )
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
