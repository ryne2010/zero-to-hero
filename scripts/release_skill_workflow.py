#!/usr/bin/env python3
"""Release and metadata helpers for the zero-to-hero skill/plugin repo."""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "zero-to-hero"
MIRROR = REPO_ROOT / "plugins" / "zero-to-hero" / "skills" / "zero-to-hero"
PLUGIN_JSON = REPO_ROOT / "plugins" / "zero-to-hero" / ".codex-plugin" / "plugin.json"
PYPROJECT = REPO_ROOT / "pyproject.toml"
RELEASE_JSONS = [SKILL / "release.json", MIRROR / "release.json"]


def parse_tag(tag: str) -> str:
    match = re.match(r"^v?(\d+\.\d+\.\d+)$", tag.strip())
    if not match:
        raise SystemExit(f"Expected semantic version tag like v0.1.0, got: {tag}")
    return match.group(1)


def parse_frontmatter(text: str, path: Path) -> dict[str, str]:
    if not text.startswith("---"):
        raise SystemExit(f"missing YAML frontmatter: {path}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SystemExit(f"malformed YAML frontmatter: {path}")
    out: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip().strip('"\'')
    return out


def yaml_scalar(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", path.read_text(encoding="utf-8"), flags=re.M)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


def pyproject_version(path: Path) -> str | None:
    if not path.exists():
        return None
    match = re.search(r'^version\s*=\s*"([^"]+)"$', path.read_text(encoding="utf-8"), flags=re.M)
    return match.group(1) if match else None


def update_skill_frontmatter(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise SystemExit(f"missing YAML frontmatter: {path}")
    parts = text.split("---", 2)
    front = parts[1].strip().splitlines()
    body = parts[2]
    out = []
    seen_version = False
    seen_license = False
    for line in front:
        if line.startswith("version:"):
            out.append(f"version: {version}")
            seen_version = True
        elif line.startswith("license:"):
            out.append("license: MIT")
            seen_license = True
        else:
            out.append(line)
    if not seen_license:
        out.append("license: MIT")
    if not seen_version:
        out.append(f"version: {version}")
    path.write_text("---\n" + "\n".join(out) + "\n---" + body, encoding="utf-8")


def update_json(path: Path, updater) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    updater(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def update_openai_yaml(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    if re.search(r"^version:", text, flags=re.M):
        text = re.sub(r"^version:.*$", f"version: {version}", text, flags=re.M)
    else:
        text = text.rstrip() + f"\nversion: {version}\n"
    path.write_text(text, encoding="utf-8")


def update_pyproject(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'^version = ".*"$', f'version = "{version}"', text, flags=re.M)
    path.write_text(text, encoding="utf-8")


def mirror_skill() -> None:
    if MIRROR.exists():
        shutil.rmtree(MIRROR)
    MIRROR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL, MIRROR)


def stamp_release(tag: str) -> None:
    version = parse_tag(tag)
    update_skill_frontmatter(SKILL / "SKILL.md", version)
    update_openai_yaml(SKILL / "agents" / "openai.yaml", version)
    update_json(SKILL / "manifest.json", lambda d: d.update({"version": version, "license": "MIT"}))
    skill_manifest = SKILL / "skill-manifest.yaml"
    text = skill_manifest.read_text(encoding="utf-8")
    if re.search(r"^version:", text, flags=re.M):
        text = re.sub(r"^version:.*$", f"version: {version}", text, flags=re.M)
    else:
        text = text.replace("name: zero-to-hero\n", f"name: zero-to-hero\nversion: {version}\n", 1)
    skill_manifest.write_text(text, encoding="utf-8")
    (SKILL / "release.json").write_text(
        json.dumps({"schema": "zero-to-hero.release.v1", "version": version, "tag": f"v{version}"}, indent=2) + "\n",
        encoding="utf-8",
    )
    update_pyproject(PYPROJECT, version)
    update_json(PLUGIN_JSON, lambda d: d.update({"version": version}))
    mirror_skill()


def validate_metadata() -> None:
    errors: list[str] = []
    versions: dict[str, str | None] = {}

    skill_md = SKILL / "SKILL.md"
    if not skill_md.exists():
        errors.append("missing skills/zero-to-hero/SKILL.md")
    else:
        versions["skill_frontmatter"] = parse_frontmatter(skill_md.read_text(encoding="utf-8"), skill_md).get("version")

    openai_yaml = SKILL / "agents" / "openai.yaml"
    versions["agents_openai_yaml"] = yaml_scalar(openai_yaml, "version")
    versions["skill_manifest_yaml"] = yaml_scalar(SKILL / "skill-manifest.yaml", "version")

    manifest_json = SKILL / "manifest.json"
    if manifest_json.exists():
        versions["skill_manifest_json"] = json.loads(manifest_json.read_text(encoding="utf-8")).get("version")
    else:
        errors.append("missing skills/zero-to-hero/manifest.json")

    if PLUGIN_JSON.exists():
        plugin = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        versions["plugin_json"] = plugin.get("version")
        if plugin.get("skills") != "./skills/":
            errors.append("plugin.json skills must be ./skills/")
        if plugin.get("name") != "zero-to-hero":
            errors.append("plugin.json name must be zero-to-hero")
    else:
        errors.append("missing plugin.json")

    versions["pyproject"] = pyproject_version(PYPROJECT)

    for path in RELEASE_JSONS:
        label = str(path.relative_to(REPO_ROOT))
        if not path.exists():
            errors.append(f"missing {label}")
        else:
            versions[label] = json.loads(path.read_text(encoding="utf-8")).get("version")

    missing_version_fields = sorted(k for k, v in versions.items() if not v)
    if missing_version_fields:
        errors.append("missing version fields: " + ", ".join(missing_version_fields))

    unique_versions = sorted({v for v in versions.values() if v})
    if len(unique_versions) != 1:
        errors.append(f"metadata versions disagree: {versions}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    print(f"metadata ok: {unique_versions[0]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    stamp = sub.add_parser("stamp-release")
    stamp.add_argument("--tag", required=True)
    sub.add_parser("mirror-skill")
    sub.add_parser("validate-metadata")
    args = parser.parse_args()
    if args.cmd == "stamp-release":
        stamp_release(args.tag)
    elif args.cmd == "mirror-skill":
        mirror_skill()
    elif args.cmd == "validate-metadata":
        validate_metadata()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
