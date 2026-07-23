#!/usr/bin/env python3
"""Run the dependency-free capability/profile fixture contract matrix."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

sys.dont_write_bytecode = True


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or ".").resolve()
    if (root / "SKILL.md").is_file():
        return root
    candidate = root / ".agents" / "skills" / "zero-to-hero"
    if (candidate / "SKILL.md").is_file():
        return candidate
    return root


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot load JSON fixture contract {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"fixture contract must contain an object: {path}")
    return value


def approved_capabilities(fixture: Path, case: dict[str, Any]) -> list[str]:
    relative = case.get("approved_capabilities_file")
    if relative is None:
        return []
    path = fixture / str(relative)
    payload = load_json(path)
    values = payload.get("approved_capabilities")
    if not isinstance(values, list) or not values or not all(
        isinstance(item, str) and item for item in values
    ):
        raise RuntimeError(
            f"{fixture.name}: approved capability data must contain a non-empty "
            "approved_capabilities string list"
        )
    return list(values)


def artifact_paths(items: Any) -> list[str]:
    if not isinstance(items, list):
        raise RuntimeError("resolved artifact collection must be a list")
    paths: list[str] = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise RuntimeError(f"resolved artifact has no string path: {item!r}")
        paths.append(item["path"])
    return sorted(paths)


def safe_relative_paths(paths: list[str]) -> bool:
    for value in paths:
        path = PurePosixPath(value)
        if path.is_absolute() or not path.parts or ".." in path.parts:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run exact capability detection, profile composition, and artifact "
            "resolution assertions against temporary fixture copies."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="skill root or repository containing .agents/skills/zero-to-hero",
    )
    parser.add_argument(
        "--case",
        action="append",
        dest="selected_cases",
        help="run one named matrix case; repeat to run multiple cases",
    )
    parser.add_argument("--json", action="store_true", help="emit full JSON results")
    args = parser.parse_args()

    skill = resolve_skill(args.path)
    scripts = skill / "scripts"
    sys.path.insert(0, str(scripts))

    try:
        from capability_detect import detect
        from zero_to_hero_contract import (
            load_graph,
            load_profiles,
            resolve_profiles,
            selected_artifacts,
        )
    except Exception as exc:
        print(f"fixture tests: failed to load contract APIs: {exc}", file=sys.stderr)
        return 1

    matrix_root = skill / "fixtures" / "profile-matrix"
    matrix_path = matrix_root / "matrix.json"
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    def check(name: str, actual: Any, expected: Any) -> None:
        ok = actual == expected
        checks.append(
            {
                "check": name,
                "ok": ok,
                "expected": expected,
                "actual": actual,
            }
        )
        if not ok:
            errors.append(f"{name}: expected {expected!r}, got {actual!r}")

    try:
        matrix = load_json(matrix_path)
        graph = load_graph(skill)
        profiles = load_profiles(skill)
    except Exception as exc:
        print(f"fixture tests: failed to load matrix/contracts: {exc}", file=sys.stderr)
        return 1

    declared_profiles = matrix.get("declared_profiles")
    cases = matrix.get("cases")
    profile_fixture_cases = matrix.get("profile_fixture_cases")
    common_required = matrix.get("common_required_paths")
    if not isinstance(declared_profiles, list) or not all(
        isinstance(item, str) for item in declared_profiles
    ):
        errors.append("matrix declared_profiles must be a string list")
        declared_profiles = []
    if not isinstance(cases, dict) or not all(
        isinstance(name, str) and isinstance(case, dict)
        for name, case in (cases or {}).items()
    ):
        errors.append("matrix cases must be an object of case objects")
        cases = {}
    if not isinstance(profile_fixture_cases, dict):
        errors.append("matrix profile_fixture_cases must be an object")
        profile_fixture_cases = {}
    if not isinstance(common_required, list) or not all(
        isinstance(item, str) for item in common_required
    ):
        errors.append("matrix common_required_paths must be a string list")
        common_required = []

    check("matrix:declared-profiles", sorted(profiles), declared_profiles)
    check(
        "matrix:base-artifact-paths",
        sorted(item["path"] for item in graph.get("base_artifacts", [])),
        common_required,
    )
    check(
        "matrix:profile-fixture-coverage",
        sorted(profile_fixture_cases),
        declared_profiles,
    )
    for profile_id, case_name in sorted(profile_fixture_cases.items()):
        if case_name not in cases:
            errors.append(
                f"matrix: profile fixture for {profile_id!r} references missing "
                f"case {case_name!r}"
            )
        elif profile_id not in cases[case_name].get("expected_profiles", []):
            errors.append(
                f"matrix: profile fixture {case_name!r} does not select {profile_id!r}"
            )

    fixture_directories = sorted(
        path.name for path in matrix_root.iterdir() if path.is_dir()
    )
    check("matrix:fixture-directories", fixture_directories, sorted(cases))

    selected_names = sorted(set(args.selected_cases or cases))
    unknown_cases = sorted(set(selected_names) - set(cases))
    if unknown_cases:
        errors.append(f"unknown fixture cases requested: {unknown_cases}")
        selected_names = [name for name in selected_names if name in cases]

    with tempfile.TemporaryDirectory(prefix="zero-to-hero-profile-fixtures-") as temp:
        temp_root = Path(temp)
        for name in selected_names:
            case = cases[name]
            source_fixture = matrix_root / name
            temp_fixture = temp_root / name
            try:
                shutil.copytree(source_fixture, temp_fixture)
                detection = detect(temp_fixture)
                approved = approved_capabilities(temp_fixture, case)
                resolution = resolve_profiles(
                    profiles,
                    repo_capabilities=detection.get("capabilities", []),
                    approved_capabilities=approved,
                    explicit_profiles=(),
                )
                artifacts = selected_artifacts(
                    graph, profiles, resolution.get("selected_profiles", [])
                )
            except Exception as exc:
                errors.append(f"{name}: fixture execution failed: {exc}")
                checks.append(
                    {
                        "check": f"{name}:execution",
                        "ok": False,
                        "error": str(exc),
                    }
                )
                continue

            check(
                f"{name}:capabilities",
                detection.get("capabilities"),
                case.get("expected_capabilities", []),
            )
            check(
                f"{name}:negative-evidence",
                detection.get("negative_evidence", {}),
                case.get("expected_negative_evidence", {}),
            )
            check(
                f"{name}:profiles",
                resolution.get("selected_profiles"),
                case.get("expected_profiles", []),
            )
            check(
                f"{name}:requires-confirmation",
                resolution.get("requires_confirmation"),
                case.get("expected_requires_confirmation", False),
            )
            absent_capabilities = case.get("expected_absent_capabilities", [])
            if absent_capabilities:
                check(
                    f"{name}:absent-capabilities",
                    sorted(
                        set(detection.get("capabilities", []))
                        & set(absent_capabilities)
                    ),
                    [],
                )
            if "expected_selection_provenance" in case:
                check(
                    f"{name}:selection-provenance",
                    resolution.get("selection_provenance"),
                    case["expected_selection_provenance"],
                )

            expected_required = sorted(
                set(common_required)
                | set(case.get("expected_required_profile_paths", []))
            )
            actual_required = artifact_paths(artifacts.get("required"))
            actual_forbidden = sorted(artifacts.get("forbidden", []))
            check(f"{name}:required-artifacts", actual_required, expected_required)
            check(
                f"{name}:forbidden-artifacts",
                actual_forbidden,
                case.get("expected_forbidden_paths", []),
            )
            check(
                f"{name}:required-forbidden-disjoint",
                sorted(set(actual_required) & set(actual_forbidden)),
                [],
            )
            check(
                f"{name}:safe-relative-artifact-paths",
                safe_relative_paths(actual_required + actual_forbidden),
                True,
            )

            evidence = detection.get("evidence", {})
            for capability, fragments in case.get(
                "expected_evidence_contains", {}
            ).items():
                actual_text = "\n".join(evidence.get(capability, []))
                for fragment in fragments:
                    ok = fragment in actual_text
                    checks.append(
                        {
                            "check": f"{name}:evidence:{capability}:{fragment}",
                            "ok": ok,
                            "expected": fragment,
                            "actual": actual_text,
                        }
                    )
                    if not ok:
                        errors.append(
                            f"{name}: {capability} evidence does not contain "
                            f"{fragment!r}: {actual_text!r}"
                        )

            if name == "generic-cmake-nonhardware":
                check(
                    f"{name}:generic-cmake-is-not-firmware",
                    "firmware" in detection.get("capabilities", []),
                    False,
                )
            if name == "ios-mobile-not-desktop":
                check(
                    f"{name}:native-ios-is-not-desktop",
                    "desktop_app" in detection.get("capabilities", []),
                    False,
                )
                check(
                    f"{name}:native-ios-does-not-select-desktop-profile",
                    "desktop-app" in resolution.get("selected_profiles", []),
                    False,
                )
            if name == "generic-dotnet-nondesktop":
                check(
                    f"{name}:generic-dotnet-is-not-desktop",
                    "desktop_app" in detection.get("capabilities", []),
                    False,
                )
                check(
                    f"{name}:generic-dotnet-does-not-select-desktop-profile",
                    "desktop-app" in resolution.get("selected_profiles", []),
                    False,
                )
            if name == "nested-fastapi-api":
                check(
                    f"{name}:nested-python-dependency-selects-api",
                    "api_backend" in detection.get("capabilities", []),
                    True,
                )
            if name == "profile-mechanical-product-approved":
                check(
                    f"{name}:greenfield-is-not-docs-first",
                    "docs-first-product" in resolution.get("selected_profiles", []),
                    False,
                )

    result = {
        "status": "fail" if errors else "pass",
        "fixture_count": len(selected_names),
        "declared_profile_count": len(declared_profiles),
        "check_count": len(checks),
        "checks": checks,
        "errors": errors,
        "temporary_copies": True,
        "generator_invoked": False,
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif errors:
        print(
            f"fixture tests: failed ({len(errors)} error(s), "
            f"{len(checks)} checks)"
        )
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print(
            f"fixture tests: passed ({len(selected_names)} fixtures, "
            f"{len(declared_profiles)} profiles, {len(checks)} checks)"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
