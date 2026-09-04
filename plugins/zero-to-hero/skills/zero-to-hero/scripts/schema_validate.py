#!/usr/bin/env python3
"""Validate executable contracts, schemas, derived views, and template coverage."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # A validator dependency gap is a release failure.
    raise SystemExit(
        "validator dependencies unavailable; run with the pinned repository "
        f"environment: {exc}"
    ) from exc

from zero_to_hero_contract import (  # noqa: E402
    artifact_phase_id,
    ContractError,
    graph_prompts,
    load_graph,
    load_json_yaml,
    load_profiles,
    rendered_contract_views,
    selected_artifacts,
    validate_artifact_phase,
    validate_global_write_exceptions,
)


def resolve_skill(path_arg: str) -> Path:
    root = Path(path_arg).resolve()
    if (root / "SKILL.md").is_file():
        return root
    candidate = root / ".agents" / "skills" / "zero-to-hero"
    if (candidate / "SKILL.md").is_file():
        return candidate
    raise SystemExit(f"cannot resolve zero-to-hero skill from {root}")


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path}: {exc}") from exc


def schema_errors(instance: Any, schema: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        return [f"{label}: invalid JSON Schema: {exc}"]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{label}:{location}: {error.message}")
    return errors


def parse_all_yaml(skill: Path) -> list[str]:
    errors: list[str] = []
    ignored_parts = {".git", "__pycache__", ".codex", ".omx", ".artifacts"}
    for path in sorted([*skill.rglob("*.yaml"), *skill.rglob("*.yml")]):
        relative = path.relative_to(skill)
        if ignored_parts & set(relative.parts):
            continue
        try:
            load_yaml(path)
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def validate_graph_and_profiles(skill: Path) -> tuple[list[str], dict[str, Any], dict[str, Any]]:
    errors: list[str] = []
    try:
        graph = load_graph(skill)
        profiles = load_profiles(skill)
    except ContractError as exc:
        return [str(exc)], {}, {}

    graph_schema = json.loads(
        (skill / "schemas/contract-graph.schema.json").read_text(encoding="utf-8")
    )
    profile_schema = json.loads(
        (skill / "schemas/output-profile.schema.json").read_text(encoding="utf-8")
    )
    planning_evidence_schema = json.loads(
        (skill / "schemas/planning-evidence.schema.json").read_text(encoding="utf-8")
    )
    manifest_schema = load_json_yaml(
        skill / "schemas/generated-files-manifest.schema.yaml"
    )
    errors.extend(schema_errors(graph, graph_schema, "contract-graph"))
    try:
        Draft202012Validator.check_schema(manifest_schema)
    except Exception as exc:
        errors.append(f"generated-files-manifest schema invalid: {exc}")
    try:
        Draft202012Validator.check_schema(planning_evidence_schema)
    except Exception as exc:
        errors.append(f"planning-evidence schema invalid: {exc}")

    for profile_id, profile in profiles.items():
        errors.extend(schema_errors(profile, profile_schema, f"profile:{profile_id}"))

    prompt_contracts = graph_prompts(graph)
    prompt_ids = [item["id"] for item in prompt_contracts]
    prompt_files = [item["prompt_file"] for item in prompt_contracts]
    if len(prompt_ids) != len(set(prompt_ids)):
        errors.append("contract graph contains duplicate prompt ids")
    if len(prompt_files) != len(set(prompt_files)):
        errors.append("contract graph contains duplicate prompt files")
    phase_orders = [item["order"] for item in graph["phases"]]
    if phase_orders != sorted(set(phase_orders)):
        errors.append("phase orders must be unique and ascending")

    for relative, expected in rendered_contract_views(graph).items():
        path = skill / relative
        if not path.is_file():
            errors.append(f"missing derived contract view: {relative}")
        elif path.read_bytes() != expected:
            errors.append(
                f"derived contract view drift: {relative}; "
                "run scripts/sync_contract_views.py --write"
            )

    expected_prompt_paths = {
        Path("prompts") / item["prompt_file"] for item in prompt_contracts
    }
    actual_prompt_paths = {
        path.relative_to(skill)
        for path in (skill / "prompts").glob("*.md")
        if path.name != "README.md"
    }
    if actual_prompt_paths != expected_prompt_paths:
        errors.append(
            "prompt file vocabulary differs from contract graph: "
            f"missing={sorted(str(p) for p in expected_prompt_paths - actual_prompt_paths)}, "
            f"extra={sorted(str(p) for p in actual_prompt_paths - expected_prompt_paths)}"
        )

    for artifact in graph["base_artifacts"]:
        source = artifact["source"]
        if source.startswith("dynamic:"):
            continue
        if not (skill / source).is_file():
            errors.append(
                f"base artifact {artifact['path']} has missing source template {source}"
            )

    profile_ids = set(profiles)
    for profile_id, profile in profiles.items():
        artifact_sets = {
            key: set(profile["artifacts"][key])
            for key in ("required", "optional", "forbidden")
        }
        if artifact_sets["required"] & artifact_sets["optional"]:
            errors.append(f"{profile_id}: required and optional artifacts overlap")
        if artifact_sets["required"] & artifact_sets["forbidden"]:
            errors.append(f"{profile_id}: required and forbidden artifacts overlap")
        if artifact_sets["optional"] & artifact_sets["forbidden"]:
            errors.append(f"{profile_id}: optional and forbidden artifacts overlap")
        for path in sorted(artifact_sets["required"]):
            if not (skill / "templates" / path).is_file():
                errors.append(f"{profile_id}: missing required template {path}")
        declared = artifact_sets["required"] | artifact_sets["optional"]
        for requirement in profile["evidence_requirements"]:
            unknown_artifacts = set(requirement["artifacts_any"]) - declared
            if unknown_artifacts:
                errors.append(
                    f"{profile_id}:{requirement['id']}: evidence references "
                    f"undeclared artifacts {sorted(unknown_artifacts)}"
                )
        compatible = set(profile["composition"]["compatible_with"])
        defaults = set(profile["composition"]["default_profiles"])
        if defaults - compatible:
            errors.append(
                f"{profile_id}: default profiles are not compatible: "
                f"{sorted(defaults - compatible)}"
            )
        for other in compatible:
            if other not in profile_ids:
                errors.append(f"{profile_id}: unknown compatible profile {other}")
            elif profile_id not in set(
                profiles[other]["composition"]["compatible_with"]
            ):
                errors.append(
                    f"profile compatibility is not symmetric: {profile_id} / {other}"
                )
        try:
            artifact_plan = selected_artifacts(graph, profiles, [profile_id])
            for artifact in artifact_plan["required"]:
                validate_artifact_phase(
                    graph,
                    path=artifact["path"],
                    phase_id=artifact["phase_id"],
                    selected_profile_ids=[profile_id],
                )
        except ContractError as exc:
            errors.append(f"{profile_id}: phase write boundary failure: {exc}")

    mutation_graph = copy.deepcopy(graph)
    try:
        readme_phase_id = artifact_phase_id(mutation_graph, "README.md", [])
        readme_phase = next(
            phase
            for phase in mutation_graph["phases"]
            if phase["id"] == readme_phase_id
        )
        readme_phase["forbidden_writes"].append("README.md")
        artifact_phase_id(mutation_graph, "README.md", [])
    except ContractError:
        pass
    else:
        errors.append(
            "phase write-boundary mutation check failed: a phase-local README.md "
            "forbidden rule did not block attribution"
        )

    exception_mutations = [
        ("wildcard", ["scripts/*.py"]),
        ("not-a-base-artifact", ["scripts/unlisted_harness.py"]),
        ("not-globally-forbidden", ["README.md"]),
    ]
    for label, exceptions in exception_mutations:
        mutated = copy.deepcopy(graph)
        mutated["global_forbidden_write_exceptions"] = exceptions
        try:
            validate_global_write_exceptions(mutated)
        except ContractError:
            pass
        else:
            errors.append(
                "global forbidden-write exception mutation check failed: "
                f"{label} exception was accepted"
            )
    missing_phase_rule = copy.deepcopy(graph)
    exception_path = missing_phase_rule["global_forbidden_write_exceptions"][0]
    for phase in missing_phase_rule["phases"]:
        phase["allowed_writes"] = [
            rule for rule in phase["allowed_writes"] if rule != exception_path
        ]
    try:
        validate_global_write_exceptions(missing_phase_rule)
    except ContractError:
        pass
    else:
        errors.append(
            "global forbidden-write exception mutation check failed: exception "
            "without an exact phase rule was accepted"
        )

    manifest = json.loads((skill / "manifest.json").read_text(encoding="utf-8"))
    expected_canonical = [
        f"prompts/{item['prompt_file']}" for item in graph["phases"]
    ]
    expected_optional = [
        f"prompts/{item['prompt_file']}" for item in graph["auxiliary_prompts"]
    ]
    if manifest.get("contract_graph") != "references/contract-graph.yaml":
        errors.append("manifest.json does not identify the canonical contract graph")
    if manifest.get("canonical_prompt_sequence") != expected_canonical:
        errors.append("manifest.json canonical prompt sequence drift")
    if manifest.get("optional_prompts") != expected_optional:
        errors.append("manifest.json optional prompt sequence drift")

    skill_manifest = load_yaml(skill / "skill-manifest.yaml")
    if skill_manifest.get("contract_graph") != "references/contract-graph.yaml":
        errors.append("skill-manifest.yaml does not identify the canonical contract graph")
    if skill_manifest.get("canonical_sequence") != expected_canonical:
        errors.append("skill-manifest.yaml canonical prompt sequence drift")
    if skill_manifest.get("optional_prompts") != expected_optional:
        errors.append("skill-manifest.yaml optional prompt sequence drift")

    forbidden_runtime_templates = [
        "templates/.omx/ultragoal/brief.md",
        "templates/.omx/ultragoal/goals.json",
        "templates/.omx/ultragoal/ledger.jsonl",
        "schemas/omx-single-goal.schema.json",
    ]
    for relative in forbidden_runtime_templates:
        if (skill / relative).exists():
            errors.append(f"runtime-owned OMX artifact is packaged: {relative}")
    return errors, graph, profiles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    skill = resolve_skill(args.skill)

    errors = parse_all_yaml(skill)
    contract_errors, graph, profiles = validate_graph_and_profiles(skill)
    errors.extend(contract_errors)
    report = {
        "status": "PASS" if not errors else "FAIL",
        "skill": str(skill),
        "yaml_files": len([*skill.rglob("*.yaml"), *skill.rglob("*.yml")]),
        "phases": len(graph.get("phases", [])),
        "prompts": len(graph_prompts(graph)) if graph else 0,
        "profiles": len(profiles),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif errors:
        print("schema and contract validation: FAIL")
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print(
            "schema and contract validation: PASS "
            f"({report['phases']} phases, {report['prompts']} prompts, "
            f"{report['profiles']} profiles)"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
