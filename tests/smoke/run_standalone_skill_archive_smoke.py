#!/usr/bin/env python3
"""Verify deterministic standalone zero-to-hero skill archive generation."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_SKILL = REPO_ROOT / "skills" / "zero-to-hero"
BUILDER = SOURCE_SKILL / "scripts" / "build_skill_zip.py"


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "zero_to_hero_build_skill_zip",
        BUILDER,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    builder = load_builder()
    with tempfile.TemporaryDirectory(prefix="zero-to-hero-standalone-smoke-") as temp:
        root = Path(temp)
        skill = root / "zero-to-hero"
        shutil.copytree(SOURCE_SKILL, skill)

        runtime_files = {
            "__pycache__/junk.pyc": b"compiled",
            ".codex/reports/zero-to-hero/report.json": b"{}",
            ".omx/state/session.json": b"{}",
            ".omx/logs/session.log": b"log",
            "generated.zip": b"not a real zip",
            "generated.zip.sha256": b"digest",
            "generated.zip.manifest.json": b"{}",
            ".generated.zip.abcd1234.tmp": b"partial archive",
        }
        for relative, content in runtime_files.items():
            path = skill / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

        archive_a = skill / "zero-to-hero-codex-skill-pack.zip"
        archive_b = root / "repeat.zip"
        result_a = builder.build_archive(skill, archive_a, run_check=False)
        first_digest = sha256_file(archive_a)
        if os.name != "nt" and stat.S_IMODE(archive_a.stat().st_mode) != 0o644:
            raise SystemExit("standalone archive has non-canonical outer permissions")

        # ZIP metadata must not inherit source mtimes.
        source = skill / "SKILL.md"
        source_stat = source.stat()
        os.utime(
            source,
            (source_stat.st_atime + 3600, source_stat.st_mtime + 3600),
        )
        result_b = builder.build_archive(skill, archive_b, run_check=False)
        second_digest = sha256_file(archive_b)
        if first_digest != second_digest:
            raise SystemExit("standalone archive is not reproducible after source mtime changes")
        if result_a["sha256"] != first_digest or result_b["sha256"] != second_digest:
            raise SystemExit("builder-reported standalone archive digest is incorrect")

        expected_paths = {
            builder.archive_name(path, skill) for path in builder.iter_files(skill, archive_a)
        }
        with zipfile.ZipFile(archive_a) as archive:
            names = archive.namelist()
            if set(names) != expected_paths:
                raise SystemExit("standalone archive contents differ from source payload")
            if archive.testzip() is not None:
                raise SystemExit("standalone archive failed integrity validation")
            if any(info.date_time != builder.STABLE_TIMESTAMP for info in archive.infolist()):
                raise SystemExit("standalone archive contains unstable timestamps")
            if any(not stat.S_ISREG(info.external_attr >> 16) for info in archive.infolist()):
                raise SystemExit("standalone archive contains non-regular entries")
            forbidden = builder.forbidden_archive_names(names)
            if forbidden:
                raise SystemExit(
                    "standalone archive contains runtime/generated files: " + ", ".join(forbidden)
                )
            if any(name.endswith(".zip") for name in names):
                raise SystemExit("standalone archive included itself or another ZIP")
            required = {
                ".agents/skills/zero-to-hero/SKILL.md",
                ".agents/skills/zero-to-hero/agents/openai.yaml",
                ".agents/skills/zero-to-hero/evals/cases.json",
                ".agents/skills/zero-to-hero/evals/handoff-quality-rubric.md",
                ".agents/skills/zero-to-hero/evals/handoff-quality-rubric.schema.json",
                ".agents/skills/zero-to-hero/scripts/build_skill_zip.py",
                ".agents/skills/zero-to-hero/scripts/run_skill_evals.py",
            }
            missing = sorted(required - set(names))
            if missing:
                raise SystemExit(
                    "standalone archive missing required contents: " + ", ".join(missing)
                )

        extract_root = root / "extracted"
        with zipfile.ZipFile(archive_a) as archive:
            archive.extractall(extract_root)
        installed_skill = extract_root / ".agents" / "skills" / "zero-to-hero"
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        rebuilt_archive = root / "rebuilt-from-standalone.zip"
        rebuild = subprocess.run(
            [
                sys.executable,
                str(installed_skill / "scripts" / "build_skill_zip.py"),
                str(installed_skill),
                "--out",
                str(rebuilt_archive),
                "--skip-check",
            ],
            cwd=extract_root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        if rebuild.returncode != 0:
            raise SystemExit(
                "standalone archive could not rebuild itself:\n" + rebuild.stdout + rebuild.stderr
            )
        if sha256_file(rebuilt_archive) != first_digest:
            raise SystemExit("standalone archive rebuild changed the canonical digest")

        check = subprocess.run(
            [
                sys.executable,
                str(installed_skill / "scripts" / "zero_to_hero_check.py"),
                str(installed_skill),
                "--summary",
            ],
            cwd=extract_root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        if check.returncode != 0:
            raise SystemExit(
                "extracted standalone skill health check failed:\n" + check.stdout + check.stderr
            )

    print("standalone skill archive smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
