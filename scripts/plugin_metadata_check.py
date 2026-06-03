#!/usr/bin/env python3
"""Validate zero-to-hero plugin, marketplace, and Codex skill metadata."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT / "plugins" / "zero-to-hero" / ".codex-plugin" / "plugin.json"
MARKETPLACE_JSON = ROOT / ".agents" / "plugins" / "marketplace.json"
SOURCE_SKILL = ROOT / "skills" / "zero-to-hero"
MIRROR_SKILL = ROOT / "plugins" / "zero-to-hero" / "skills" / "zero-to-hero"
OPENAI_YAML = SOURCE_SKILL / "agents" / "openai.yaml"
PYPROJECT = ROOT / "pyproject.toml"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to parse JSON {path.relative_to(ROOT)}: {exc}") from exc


def yaml_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, flags=re.M)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


def frontmatter_version(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    for line in parts[1].splitlines():
        if line.strip().startswith("version:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    return None


def pyproject_version(path: Path) -> str | None:
    if not path.exists():
        return None
    match = re.search(r'^version\s*=\s*"([^"]+)"$', path.read_text(encoding="utf-8"), flags=re.M)
    return match.group(1) if match else None


def release_json_version(path: Path) -> str | None:
    if not path.exists():
        return None
    data = load_json(path)
    return data.get("version") if isinstance(data.get("version"), str) else None


def main() -> int:
    errors: list[str] = []
    versions: dict[str, str | None] = {}

    if not PLUGIN_JSON.exists():
        errors.append("missing plugins/zero-to-hero/.codex-plugin/plugin.json")
        plugin: dict = {}
    else:
        plugin = load_json(PLUGIN_JSON)

    if not MARKETPLACE_JSON.exists():
        errors.append("missing .agents/plugins/marketplace.json")
        marketplace: dict = {}
    else:
        marketplace = load_json(MARKETPLACE_JSON)

    for path, label in [(SOURCE_SKILL, "source skill"), (MIRROR_SKILL, "plugin mirror skill")]:
        if not (path / "SKILL.md").exists():
            errors.append(f"missing {label} SKILL.md: {path.relative_to(ROOT)}")

    if plugin:
        expected_scalars = {
            "name": "zero-to-hero",
            "license": "MIT",
            "skills": "./skills/",
        }
        for key, expected in expected_scalars.items():
            if plugin.get(key) != expected:
                errors.append(f"plugin.json {key} must be {expected!r}, got {plugin.get(key)!r}")
        version = plugin.get("version")
        if not isinstance(version, str) or not SEMVER.match(version):
            errors.append(f"plugin.json version must be semver X.Y.Z, got {version!r}")
        versions["plugin_json"] = version if isinstance(version, str) else None
        interface = plugin.get("interface")
        if not isinstance(interface, dict):
            errors.append("plugin.json interface must be an object")
        else:
            for key in ["displayName", "shortDescription", "longDescription", "developerName", "category", "defaultPrompt"]:
                if key not in interface:
                    errors.append(f"plugin.json interface missing {key}")
            capabilities = interface.get("capabilities")
            if not isinstance(capabilities, list) or not capabilities:
                errors.append("plugin.json interface.capabilities must be a non-empty list")
            if interface.get("displayName") != "zero-to-hero":
                errors.append("plugin.json interface.displayName must be zero-to-hero")

    if marketplace:
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            errors.append("marketplace.json plugins must be a non-empty list")
        else:
            entry = next((item for item in plugins if isinstance(item, dict) and item.get("name") == "zero-to-hero"), None)
            if entry is None:
                errors.append("marketplace.json must contain a zero-to-hero plugin entry")
            else:
                source = entry.get("source")
                if not isinstance(source, dict):
                    errors.append("marketplace zero-to-hero entry source must be an object")
                else:
                    if source.get("source") != "local":
                        errors.append("marketplace zero-to-hero source.source must be local")
                    if source.get("path") != "./plugins/zero-to-hero":
                        errors.append("marketplace zero-to-hero source.path must be ./plugins/zero-to-hero")
                policy = entry.get("policy")
                if not isinstance(policy, dict):
                    errors.append("marketplace zero-to-hero policy must be an object")
                else:
                    if policy.get("installation") != "AVAILABLE":
                        errors.append("marketplace zero-to-hero policy.installation must be AVAILABLE")

    if not OPENAI_YAML.exists():
        errors.append("missing skills/zero-to-hero/agents/openai.yaml")
    else:
        text = OPENAI_YAML.read_text(encoding="utf-8")
        versions["agents_openai_yaml"] = yaml_scalar(text, "version")
        if "allow_implicit_invocation: false" not in text:
            errors.append("agents/openai.yaml must set allow_implicit_invocation: false")
        for label, pattern in {
            "icon_small": r"icon_small:\s*\"?([^\"\n]+)\"?",
            "icon_large": r"icon_large:\s*\"?([^\"\n]+)\"?",
        }.items():
            match = re.search(pattern, text)
            if not match:
                errors.append(f"agents/openai.yaml missing {label}")
                continue
            icon = match.group(1).strip().strip('"\'')
            icon_path = (SOURCE_SKILL / icon.removeprefix("./")).resolve()
            try:
                icon_path.relative_to(SOURCE_SKILL.resolve())
            except ValueError:
                errors.append(f"agents/openai.yaml {label} must stay inside skill root: {icon}")
                continue
            if not icon_path.exists():
                errors.append(f"agents/openai.yaml {label} does not resolve: {icon}")
        if "default_prompt:" not in text:
            errors.append("agents/openai.yaml missing default_prompt")

    versions["skill_frontmatter"] = frontmatter_version(SOURCE_SKILL / "SKILL.md") if (SOURCE_SKILL / "SKILL.md").exists() else None
    versions["skill_manifest_yaml"] = yaml_scalar((SOURCE_SKILL / "skill-manifest.yaml").read_text(encoding="utf-8"), "version") if (SOURCE_SKILL / "skill-manifest.yaml").exists() else None
    if (SOURCE_SKILL / "manifest.json").exists():
        data = load_json(SOURCE_SKILL / "manifest.json")
        versions["skill_manifest_json"] = data.get("version") if isinstance(data.get("version"), str) else None
    else:
        versions["skill_manifest_json"] = None
    versions["pyproject"] = pyproject_version(PYPROJECT)
    versions["source_release_json"] = release_json_version(SOURCE_SKILL / "release.json")
    versions["mirror_release_json"] = release_json_version(MIRROR_SKILL / "release.json")

    missing_versions = sorted(key for key, value in versions.items() if not value)
    if missing_versions:
        errors.append("missing version metadata: " + ", ".join(missing_versions))
    unique_versions = sorted({value for value in versions.values() if value})
    if len(unique_versions) != 1:
        errors.append("metadata versions disagree: " + json.dumps(versions, sort_keys=True))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(json.dumps({"status": "pass", "version": unique_versions[0], "checked": sorted(versions)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
