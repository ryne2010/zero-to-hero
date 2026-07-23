#!/usr/bin/env python3
"""Build a deterministic, standalone zero-to-hero skill archive."""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ARCHIVE_PREFIX = PurePosixPath(".agents/skills/zero-to-hero")
STABLE_TIMESTAMP = (2024, 1, 1, 0, 0, 0)
EXCLUDED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
}
EXCLUDED_FILE_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
OMX_RUNTIME_DIR_NAMES = {"hud", "logs", "state"}


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or ".").resolve()
    if (root / "SKILL.md").exists():
        return root
    candidate = root / ".agents" / "skills" / "zero-to-hero"
    if (candidate / "SKILL.md").exists():
        return candidate
    return root


def is_omx_runtime_path(rel: Path) -> bool:
    parts = rel.parts
    for index, part in enumerate(parts[:-1]):
        if part == ".omx" and parts[index + 1] in OMX_RUNTIME_DIR_NAMES:
            return True
    return False


def should_exclude(path: Path, skill: Path, output: Path | None = None) -> bool:
    rel = path.relative_to(skill)
    if output is not None and path.resolve() == output.resolve():
        return True
    if (
        output is not None
        and path.parent.resolve() == output.parent.resolve()
        and path.name.startswith(f".{output.name}.")
        and path.name.endswith(".tmp")
    ):
        return True
    if path.is_symlink():
        return True
    if any(part in EXCLUDED_DIR_NAMES for part in rel.parts):
        return True
    if ".codex" in rel.parts:
        return True
    if is_omx_runtime_path(rel):
        return True
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if path.name.endswith((".zip.sha256", ".zip.manifest.json")):
        return True
    if path.name.startswith(".") and ".zip." in path.name and path.name.endswith(".tmp"):
        return True
    return False


def iter_files(skill: Path, output: Path | None = None) -> list[Path]:
    files = [
        path
        for path in skill.rglob("*")
        if path.is_file() and not should_exclude(path, skill, output)
    ]
    return sorted(files, key=lambda path: path.relative_to(skill).as_posix())


def archive_mode(rel: Path) -> int:
    if rel.parts and rel.parts[0] == "scripts":
        return 0o755
    return 0o644


def archive_name(path: Path, skill: Path) -> str:
    rel = PurePosixPath(path.relative_to(skill).as_posix())
    return str(ARCHIVE_PREFIX / rel)


def write_zip(output: Path, skill: Path, files: list[Path]) -> None:
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            rel = path.relative_to(skill)
            info = zipfile.ZipInfo(archive_name(path, skill))
            info.date_time = STABLE_TIMESTAMP
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | archive_mode(rel)) << 16
            archive.writestr(info, path.read_bytes())


def forbidden_archive_names(names: list[str]) -> list[str]:
    forbidden: list[str] = []
    for name in names:
        path = PurePosixPath(name)
        parts = path.parts
        if any(part in EXCLUDED_DIR_NAMES for part in parts):
            forbidden.append(name)
            continue
        if ".codex" in parts:
            forbidden.append(name)
            continue
        if any(
            part == ".omx" and index + 1 < len(parts) and parts[index + 1] in OMX_RUNTIME_DIR_NAMES
            for index, part in enumerate(parts)
        ):
            forbidden.append(name)
            continue
        if path.name in EXCLUDED_FILE_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
            forbidden.append(name)
            continue
        if path.name.endswith((".zip.sha256", ".zip.manifest.json")):
            forbidden.append(name)
            continue
        if path.name.startswith(".") and ".zip." in path.name and path.name.endswith(".tmp"):
            forbidden.append(name)
    return forbidden


def validate_archive(output: Path, skill: Path, files: list[Path]) -> None:
    expected_names = [archive_name(path, skill) for path in files]
    required_names = {
        str(ARCHIVE_PREFIX / "SKILL.md"),
        str(ARCHIVE_PREFIX / "agents/openai.yaml"),
        str(ARCHIVE_PREFIX / "evals/cases.json"),
        str(ARCHIVE_PREFIX / "evals/handoff-quality-rubric.schema.json"),
        str(ARCHIVE_PREFIX / "scripts/build_skill_zip.py"),
        str(ARCHIVE_PREFIX / "scripts/run_skill_evals.py"),
    }
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        duplicate_names = sorted({name for name in names if names.count(name) > 1})
        missing = sorted(required_names - set(names))
        forbidden = forbidden_archive_names(names)
        bad_member = archive.testzip()
        unstable_timestamps = sorted(
            info.filename for info in archive.infolist() if info.date_time != STABLE_TIMESTAMP
        )
        wrong_modes = sorted(
            info.filename
            for info in archive.infolist()
            if ((info.external_attr >> 16) & 0o777)
            != archive_mode(Path(info.filename).relative_to(Path(ARCHIVE_PREFIX)))
        )
        wrong_types = sorted(
            info.filename
            for info in archive.infolist()
            if not stat.S_ISREG(info.external_attr >> 16)
        )
    if names != expected_names:
        raise SystemExit("standalone archive file list differs from the canonical source file list")
    if duplicate_names:
        raise SystemExit(
            "standalone archive contains duplicate entries: " + ", ".join(duplicate_names)
        )
    if missing:
        raise SystemExit("standalone archive missing required files: " + ", ".join(missing))
    if forbidden:
        raise SystemExit(
            "standalone archive contains generated/runtime artifacts: " + ", ".join(forbidden[:10])
        )
    if bad_member:
        raise SystemExit(f"standalone archive integrity failure at {bad_member}")
    if unstable_timestamps:
        raise SystemExit(
            "standalone archive contains non-deterministic timestamps: "
            + ", ".join(unstable_timestamps[:10])
        )
    if wrong_modes:
        raise SystemExit(
            "standalone archive contains non-canonical permissions: " + ", ".join(wrong_modes[:10])
        )
    if wrong_types:
        raise SystemExit(
            "standalone archive contains non-regular entries: " + ", ".join(wrong_types[:10])
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_skill_check(skill: Path) -> None:
    check = skill / "scripts" / "zero_to_hero_check.py"
    if not check.exists():
        return
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, str(check), str(skill), "--summary"],
        cwd=skill,
        env=env,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def build_archive(skill: Path, output: Path, *, run_check: bool = True) -> dict[str, object]:
    if not (skill / "SKILL.md").exists():
        raise SystemExit(f"could not locate skill root: {skill}")
    if run_check:
        run_skill_check(skill)

    output = output.resolve()
    files = iter_files(skill, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
        write_zip(temporary_path, skill, files)
        validate_archive(temporary_path, skill, files)
        temporary_path.chmod(0o644)
        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return {
        "status": "PASS",
        "archive": str(output),
        "file_count": len(files),
        "sha256": sha256_file(output),
        "deterministic_timestamp": "2024-01-01T00:00:00",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a deterministic ZIP for the zero-to-hero skill directory."
    )
    parser.add_argument(
        "skill",
        nargs="?",
        default=".",
        help="skill root or repo containing .agents/skills/zero-to-hero",
    )
    parser.add_argument("--out", default="zero-to-hero-codex-skill-pack.zip")
    parser.add_argument("--skip-check", action="store_true")
    args = parser.parse_args()

    skill = resolve_skill(args.skill)
    result = build_archive(skill, Path(args.out), run_check=not args.skip_check)
    print(
        f"built {result['archive']} with {result['file_count']} files (sha256={result['sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
