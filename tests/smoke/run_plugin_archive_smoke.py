#!/usr/bin/env python3
"""Smoke-test deterministic plugin release archive generation and sidecars."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

# Keep smoke tests from leaving runtime cache artifacts in the packaged repo.
sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "build_plugin_archive.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("zero_to_hero_build_plugin_archive", SCRIPT)
    if spec is None or spec.loader is None:
        raise SystemExit("unable to load archive builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_archive_direct(builder, output: Path) -> dict:
    version = builder.package_version()
    files = builder.iter_files(list(builder.DEFAULT_INCLUDE_PATHS))
    mirror_errors = builder.mirror_parity_errors()
    if mirror_errors:
        print("source/plugin mirror parity failed before archive smoke:", file=sys.stderr)
        print("\n".join(mirror_errors[:20]), file=sys.stderr)
        raise SystemExit(1)
    builder.write_zip(output, files)
    builder.validate_archive(output)
    sidecars = builder.write_release_sidecars(output, files, version)
    return {"status": "pass", "version": version, "file_count": len(files), **sidecars}


def expect_system_exit(action, expected_text: str) -> None:
    try:
        action()
    except SystemExit as exc:
        if expected_text not in str(exc):
            print(f"unexpected rejection message: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
    else:
        print(f"expected rejection containing {expected_text!r}", file=sys.stderr)
        raise SystemExit(1)


def run_archive_safety_regressions(builder) -> None:
    with tempfile.TemporaryDirectory(dir=REPO_ROOT, prefix=".archive-safety-") as included_dir:
        included_root = Path(included_dir)
        included_rel = included_root.relative_to(REPO_ROOT).as_posix()
        ordinary_file = included_root / "ordinary.txt"
        ordinary_file.write_text("inside\n", encoding="utf-8")
        ordinary_file.chmod(0o777)
        with tempfile.TemporaryDirectory(prefix="zero-to-hero-mode-") as mode_dir:
            mode_archive = Path(mode_dir) / "mode.zip"
            builder.write_zip(mode_archive, [ordinary_file])
            with zipfile.ZipFile(mode_archive) as zf:
                mode_info = zf.infolist()[0]
            archived_mode = stat.S_IMODE(mode_info.external_attr >> 16)
            if archived_mode != 0o644:
                print(
                    f"host executable bit leaked into canonical archive metadata: {oct(archived_mode)}",
                    file=sys.stderr,
                )
                raise SystemExit(1)

        with tempfile.TemporaryDirectory(prefix="zero-to-hero-external-") as external_dir:
            external_file = Path(external_dir) / "secret.txt"
            external_file.write_text("must not leak\n", encoding="utf-8")
            expect_system_exit(
                lambda: builder.iter_files([str(external_file)]),
                "escapes repository root",
            )

            symlink_path = included_root / "external-secret.txt"
            try:
                symlink_path.symlink_to(external_file)
            except (NotImplementedError, OSError) as exc:
                if os.name != "nt":
                    print(f"unable to create symlink regression fixture: {exc}", file=sys.stderr)
                    raise SystemExit(1) from exc
            else:
                expect_system_exit(
                    lambda: builder.iter_files([included_rel]),
                    "symlink is not allowed",
                )
                expect_system_exit(
                    lambda: builder.write_zip(included_root / "leak.zip", [symlink_path]),
                    "symlink is not allowed",
                )


def validate_zip_metadata(builder, archive: Path) -> None:
    expected_examples = {
        "README.md": 0o644,
        "scripts/build_plugin_archive.py": 0o755,
        "scripts/release_skill_workflow.py": 0o644,
        "skills/zero-to-hero/scripts/build_skill_zip.py": 0o755,
        "plugins/zero-to-hero/skills/zero-to-hero/scripts/build_skill_zip.py": 0o755,
        "tests/smoke/run_skill_smoke.py": 0o644,
    }
    observed_modes: dict[str, int] = {}
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.create_system != 3:
                print(
                    f"zip entry has non-Unix create_system metadata: {info.filename}",
                    file=sys.stderr,
                )
                raise SystemExit(1)
            unix_mode = info.external_attr >> 16
            if stat.S_IFMT(unix_mode) != stat.S_IFREG:
                print(
                    f"zip entry is not marked as a regular file: {info.filename}", file=sys.stderr
                )
                raise SystemExit(1)
            permissions = stat.S_IMODE(unix_mode)
            expected_mode = builder.canonical_zip_mode(Path(info.filename))
            if permissions != expected_mode:
                print(
                    f"zip entry mode mismatch for {info.filename}: expected {oct(expected_mode)}, got {oct(permissions)}",
                    file=sys.stderr,
                )
                raise SystemExit(1)
            if permissions == 0o755 and not builder.is_intended_executable(Path(info.filename)):
                print(f"unexpected executable archive entry: {info.filename}", file=sys.stderr)
                raise SystemExit(1)
            if info.date_time != (2024, 1, 1, 0, 0, 0):
                print(f"zip entry timestamp is not canonical: {info.filename}", file=sys.stderr)
                raise SystemExit(1)
            observed_modes[info.filename] = permissions

    for path, expected_mode in expected_examples.items():
        if observed_modes.get(path) != expected_mode:
            print(
                f"expected canonical mode {oct(expected_mode)} for {path}, got {observed_modes.get(path)!r}",
                file=sys.stderr,
            )
            raise SystemExit(1)


def validate_archive(archive: Path) -> tuple[str, dict]:
    sha_path = archive.with_suffix(archive.suffix + ".sha256")
    manifest_path = archive.with_suffix(archive.suffix + ".manifest.json")
    if not archive.exists():
        print(f"missing archive: {archive}", file=sys.stderr)
        raise SystemExit(1)
    if not sha_path.exists():
        print("missing sha256 sidecar", file=sys.stderr)
        raise SystemExit(1)
    if not manifest_path.exists():
        print("missing archive manifest sidecar", file=sys.stderr)
        raise SystemExit(1)

    actual_digest = sha256_file(archive)
    sidecar_digest = sha_path.read_text(encoding="utf-8").split()[0]
    if sidecar_digest != actual_digest:
        print("sha256 sidecar does not match archive", file=sys.stderr)
        raise SystemExit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("archive") != archive.name:
        print("archive manifest has wrong archive name", file=sys.stderr)
        raise SystemExit(1)
    if manifest.get("archive_sha256") != actual_digest:
        print("archive manifest sha256 does not match archive", file=sys.stderr)
        raise SystemExit(1)
    included_paths = manifest.get("included_paths")
    if not isinstance(included_paths, list) or not included_paths:
        print("archive manifest missing included_paths", file=sys.stderr)
        raise SystemExit(1)
    if len(set(included_paths)) != len(included_paths):
        print("archive manifest included_paths contains duplicates", file=sys.stderr)
        raise SystemExit(1)
    if manifest.get("file_count") != len(included_paths):
        print("archive manifest file_count does not match included_paths", file=sys.stderr)
        raise SystemExit(1)

    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        required = {
            "plugins/zero-to-hero/.codex-plugin/plugin.json",
            "plugins/zero-to-hero/skills/zero-to-hero/SKILL.md",
            "skills/zero-to-hero/SKILL.md",
            ".agents/plugins/marketplace.json",
            "AGENTS.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "scripts/build_plugin_archive.py",
            "scripts/release_skill_workflow.py",
            "tests/check_skill_mirror.py",
            "tests/smoke/run_skill_smoke.py",
            ".github/workflows/validate.yml",
        }
        missing = sorted(required - names)
        forbidden = [
            n
            for n in names
            if "__pycache__" in n
            or n.endswith((".pyc", ".pyo"))
            or n.startswith("dist/")
            or n.startswith(".codex/")
        ]
        bad = zf.testzip()
        if set(included_paths) != names:
            missing_from_manifest = sorted(names - set(included_paths))[:10]
            missing_from_zip = sorted(set(included_paths) - names)[:10]
            print(
                f"archive manifest/zip path mismatch; missing_from_manifest={missing_from_manifest}; missing_from_zip={missing_from_zip}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        files = manifest.get("files")
        if files is not None:
            if not isinstance(files, list) or len(files) != len(included_paths):
                print(
                    "archive manifest files list must match included_paths length", file=sys.stderr
                )
                raise SystemExit(1)
            by_path = {item.get("path"): item for item in files if isinstance(item, dict)}
            if set(by_path) != set(included_paths):
                print(
                    "archive manifest files list paths do not match included_paths", file=sys.stderr
                )
                raise SystemExit(1)
            for path_name, item in by_path.items():
                data = zf.read(path_name)
                if item.get("size_bytes") != len(data):
                    print(f"archive manifest size mismatch for {path_name}", file=sys.stderr)
                    raise SystemExit(1)
                if item.get("sha256") != hashlib.sha256(data).hexdigest():
                    print(f"archive manifest sha256 mismatch for {path_name}", file=sys.stderr)
                    raise SystemExit(1)
    builder = load_builder()
    validate_zip_metadata(builder, archive)
    if missing:
        print(f"missing from archive: {missing}", file=sys.stderr)
        raise SystemExit(1)
    if forbidden:
        print(f"forbidden runtime/generated artifacts: {forbidden[:10]}", file=sys.stderr)
        raise SystemExit(1)
    if bad:
        print(f"zip integrity failure: {bad}", file=sys.stderr)
        raise SystemExit(1)
    return actual_digest, manifest


def comparable_manifest(manifest: dict) -> dict:
    """Normalize fields that intentionally differ by output archive name."""
    out = dict(manifest)
    out.pop("archive", None)
    out.pop("archive_sha256", None)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repeat", type=int, default=2, help="Number of archive builds to compare for determinism."
    )
    parser.add_argument(
        "--archive",
        help="Validate an existing archive and sidecars instead of building temp archives.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Accepted for Makefile compatibility; direct smoke path does not spawn a build subprocess.",
    )
    args = parser.parse_args()
    if args.repeat < 1:
        raise SystemExit("--repeat must be >= 1")

    if args.archive:
        archive = Path(args.archive)
        if not archive.is_absolute():
            archive = (REPO_ROOT / archive).resolve()
        digest, manifest = validate_archive(archive)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "archive": str(archive),
                    "archive_sha256": digest,
                    "file_count": manifest.get("file_count"),
                },
                indent=2,
            )
        )
        return 0

    builder = load_builder()
    run_archive_safety_regressions(builder)
    digests: list[str] = []
    manifests: list[dict] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for index in range(args.repeat):
            archive = root / f"zero-to-hero-test-{index}.zip"
            payload = build_archive_direct(builder, archive)
            if payload.get("status") != "pass":
                print(json.dumps(payload, indent=2), file=sys.stderr)
                raise SystemExit(1)
            digest, manifest = validate_archive(archive)
            digests.append(digest)
            manifests.append(manifest)

    if len(set(digests)) != 1:
        print("archive is not deterministic across repeated builds", file=sys.stderr)
        raise SystemExit(1)
    first = comparable_manifest(manifests[0])
    for manifest in manifests[1:]:
        if comparable_manifest(manifest) != first:
            print(
                "archive manifests differ across repeated builds beyond archive name/digest",
                file=sys.stderr,
            )
            raise SystemExit(1)
    print("plugin archive smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
