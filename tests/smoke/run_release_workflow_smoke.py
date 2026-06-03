#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_release_workflow():
    path = ROOT / "scripts" / "release_skill_workflow.py"
    spec = importlib.util.spec_from_file_location("zero_to_hero_release_skill_workflow", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def main() -> int:
    # Directly invoke the release metadata validator instead of spawning a nested
    # subprocess. This keeps make validate bounded and avoids subprocess flakiness
    # in constrained Codex/OMX sandboxes.
    release = load_release_workflow()
    release.validate_metadata()

    plugin = json.loads((ROOT / "plugins" / "zero-to-hero" / ".codex-plugin" / "plugin.json").read_text())
    assert plugin["name"] == "zero-to-hero"
    assert plugin["skills"] == "./skills/"
    assert plugin["interface"]["displayName"] == "zero-to-hero"
    print("release workflow smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
