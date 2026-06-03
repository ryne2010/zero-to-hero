#!/usr/bin/env python3
"""Smoke-test deterministic plugin release archive generation and sidecars."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
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
            n for n in names
            if "__pycache__" in n or n.endswith((".pyc", ".pyo")) or n.startswith("dist/") or n.startswith(".codex/")
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
                print("archive manifest files list must match included_paths length", file=sys.stderr)
                raise SystemExit(1)
            by_path = {item.get("path"): item for item in files if isinstance(item, dict)}
            if set(by_path) != set(included_paths):
                print("archive manifest files list paths do not match included_paths", file=sys.stderr)
                raise SystemExit(1)
            for path_name, item in by_path.items():
                data = zf.read(path_name)
                if item.get("size_bytes") != len(data):
                    print(f"archive manifest size mismatch for {path_name}", file=sys.stderr)
                    raise SystemExit(1)
                if item.get("sha256") != hashlib.sha256(data).hexdigest():
                    print(f"archive manifest sha256 mismatch for {path_name}", file=sys.stderr)
                    raise SystemExit(1)
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
    parser.add_argument("--repeat", type=int, default=2, help="Number of archive builds to compare for determinism.")
    parser.add_argument("--archive", help="Validate an existing archive and sidecars instead of building temp archives.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Accepted for Makefile compatibility; direct smoke path does not spawn a build subprocess.")
    args = parser.parse_args()
    if args.repeat < 1:
        raise SystemExit("--repeat must be >= 1")

    if args.archive:
        archive = Path(args.archive)
        if not archive.is_absolute():
            archive = (REPO_ROOT / archive).resolve()
        digest, manifest = validate_archive(archive)
        print(json.dumps({"status": "pass", "archive": str(archive), "archive_sha256": digest, "file_count": manifest.get("file_count")}, indent=2))
        return 0

    builder = load_builder()
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
            print("archive manifests differ across repeated builds beyond archive name/digest", file=sys.stderr)
            raise SystemExit(1)
    print("plugin archive smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
