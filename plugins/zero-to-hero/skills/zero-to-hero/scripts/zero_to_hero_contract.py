#!/usr/bin/env python3
"""Load and render zero-to-hero's executable phase and profile contracts."""
from __future__ import annotations

import hashlib
import fnmatch
import json
import re
from pathlib import Path
from typing import Any, Iterable

CONTRACT_REL = Path("references/contract-graph.yaml")
PROFILE_DIR_REL = Path("references/output-profiles")
CAPABILITY_RULES_REL = Path("references/capability-rules.yaml")
CAPABILITY_TOKEN_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
DETECTOR_META_CAPABILITIES = {
    "ci",
    "containerized",
    "database",
    "monorepo",
    "omx",
    "repo_scoped_skills",
    "unknown",
}


class ContractError(RuntimeError):
    """Raised when an executable zero-to-hero contract is invalid."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ContractError(f"duplicate key in JSON-compatible YAML: {key}")
        out[key] = value
    return out


def load_json_yaml(path: Path) -> dict[str, Any]:
    """Load a JSON document stored with a YAML extension.

    JSON is a YAML 1.2 subset. Keeping executable contracts in this subset gives
    runtime scripts a dependency-free loader while the release gate still runs
    full YAML and JSON Schema validation with pinned dependencies.
    """

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path} must contain an object")
    return value


def skill_root_from(path: str | Path) -> Path:
    root = Path(path).resolve()
    if (root / "SKILL.md").is_file():
        return root
    candidate = root / ".agents" / "skills" / "zero-to-hero"
    if (candidate / "SKILL.md").is_file():
        return candidate
    raise ContractError(f"cannot resolve zero-to-hero skill root from {root}")


def load_graph(skill: Path) -> dict[str, Any]:
    graph = load_json_yaml(skill / CONTRACT_REL)
    prompts = graph_prompts(graph)
    ids = [item["id"] for item in prompts]
    orders = [item["order"] for item in prompts]
    files = [item["prompt_file"] for item in prompts]
    for label, values in (("id", ids), ("order", orders), ("prompt_file", files)):
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            raise ContractError(f"duplicate prompt {label}: {duplicates}")
    phase_orders = [item["order"] for item in graph.get("phases", [])]
    if phase_orders != sorted(phase_orders):
        raise ContractError("phase order must be strictly ascending in contract graph")
    prompt_ids = set(ids)
    for group, members in graph.get("prompt_groups", {}).items():
        missing = [member for member in members if member not in prompt_ids]
        if missing:
            raise ContractError(f"prompt group {group!r} references unknown ids: {missing}")
    return graph


def graph_prompts(graph: dict[str, Any]) -> list[dict[str, Any]]:
    prompts = [*graph.get("phases", []), *graph.get("auxiliary_prompts", [])]
    if not all(isinstance(item, dict) for item in prompts):
        raise ContractError("all phase and auxiliary prompt entries must be objects")
    return sorted(prompts, key=lambda item: (int(item["order"]), str(item["id"])))


def prompt_by_id(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in graph_prompts(graph)}


def load_profiles(skill: Path) -> dict[str, dict[str, Any]]:
    profile_dir = skill / PROFILE_DIR_REL
    if not profile_dir.is_dir():
        raise ContractError(f"missing profile directory: {profile_dir}")
    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted(profile_dir.glob("*.yaml")):
        data = load_json_yaml(path)
        profile_id = data.get("id")
        if not isinstance(profile_id, str) or not profile_id:
            raise ContractError(f"profile {path} has no string id")
        if path.stem != profile_id:
            raise ContractError(
                f"profile filename/id mismatch: {path.name} contains {profile_id!r}"
            )
        if profile_id in profiles:
            raise ContractError(f"duplicate profile id: {profile_id}")
        profiles[profile_id] = data
    if not profiles:
        raise ContractError("no output profiles found")
    for profile_id, profile in profiles.items():
        for related in (
            profile.get("composition", {}).get("compatible_with", [])
            + profile.get("composition", {}).get("default_profiles", [])
        ):
            if related not in profiles:
                raise ContractError(
                    f"profile {profile_id!r} references unknown profile {related!r}"
                )
    return profiles


def canonical_capabilities(
    skill: Path,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> set[str]:
    """Return the executable capability vocabulary from rules and profiles."""

    rules = load_json_yaml(skill / CAPABILITY_RULES_REL)
    capabilities: set[str] = set(DETECTOR_META_CAPABILITIES)
    for field in (
        "package_dependencies",
        "python_dependencies",
        "file_globs",
        "content_rules",
    ):
        value = rules.get(field)
        if not isinstance(value, dict):
            raise ContractError(f"capability rules field {field!r} must be an object")
        capabilities.update(str(item) for item in value)
    for profile in (profiles or load_profiles(skill)).values():
        capabilities.update(profile.get("detect", {}).get("capabilities_any", []))
        capabilities.update(profile.get("detect", {}).get("capabilities_all", []))
        capabilities.update(profile.get("approved", {}).get("capabilities_any", []))
    invalid = sorted(
        item
        for item in capabilities
        if not isinstance(item, str) or not CAPABILITY_TOKEN_RE.fullmatch(item)
    )
    if invalid:
        raise ContractError(f"canonical capability vocabulary has unsafe tokens: {invalid}")
    if not capabilities:
        raise ContractError("canonical capability vocabulary is empty")
    return capabilities


def validate_capability_tokens(
    skill: Path,
    values: Iterable[str],
    *,
    label: str,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    """Validate capability data before it reaches generated instructions."""

    tokens = [str(item) for item in values]
    unsafe = sorted(
        set(item for item in tokens if not CAPABILITY_TOKEN_RE.fullmatch(item))
    )
    if unsafe:
        raise ContractError(f"{label} contain unsafe capability tokens: {unsafe}")
    canonical = canonical_capabilities(skill, profiles)
    unknown = sorted(set(tokens) - canonical)
    if unknown:
        raise ContractError(
            f"{label} contain capabilities outside the canonical vocabulary: {unknown}"
        )
    return sorted(set(tokens))


def _profile_matches(
    profile: dict[str, Any],
    repo_capabilities: set[str],
    approved_capabilities: set[str],
) -> tuple[bool, list[str]]:
    detect = profile.get("detect", {})
    repo_any = set(detect.get("capabilities_any", []))
    repo_all = set(detect.get("capabilities_all", []))
    approved_any = set(profile.get("approved", {}).get("capabilities_any", []))
    repo_match = (not repo_all or repo_all <= repo_capabilities) and (
        not repo_any or bool(repo_any & repo_capabilities)
    )
    approved_match = bool(approved_any & approved_capabilities)
    reasons: list[str] = []
    if repo_match and (repo_any or repo_all):
        reasons.append("repository_evidence")
    if approved_match:
        reasons.append("approved_capability")
    return bool(reasons), reasons


def _expand_default_profiles(
    selected: list[str],
    profiles: dict[str, dict[str, Any]],
) -> list[str]:
    out = list(selected)
    cursor = 0
    while cursor < len(out):
        profile_id = out[cursor]
        cursor += 1
        for implied in profiles[profile_id].get("composition", {}).get(
            "default_profiles", []
        ):
            if implied not in out:
                out.append(implied)
    return out


def resolve_profiles(
    profiles: dict[str, dict[str, Any]],
    repo_capabilities: Iterable[str] = (),
    approved_capabilities: Iterable[str] = (),
    explicit_profiles: Iterable[str] = (),
) -> dict[str, Any]:
    repo_caps = {str(item) for item in repo_capabilities}
    approved_caps = {str(item) for item in approved_capabilities}
    explicit = [str(item) for item in explicit_profiles]
    unknown = sorted(set(explicit) - set(profiles))
    if unknown:
        raise ContractError(f"unknown explicit profiles: {unknown}")

    provenance: dict[str, list[str]] = {}
    selected: list[str] = []
    if explicit:
        selected = list(dict.fromkeys(explicit))
        provenance.update({profile_id: ["explicit_profile"] for profile_id in selected})
    else:
        for profile_id, profile in profiles.items():
            matched, reasons = _profile_matches(profile, repo_caps, approved_caps)
            if matched:
                selected.append(profile_id)
                provenance[profile_id] = reasons

    selected = _expand_default_profiles(selected, profiles)
    for profile_id in selected:
        provenance.setdefault(profile_id, ["profile_default"])

    requires_confirmation = False
    warnings: list[str] = []
    if not selected:
        if approved_caps:
            raise ContractError(
                "approved capabilities do not match any output profile: "
                + ", ".join(sorted(approved_caps))
            )
        docs_profile = profiles.get("docs-first-product")
        docs_markers = set(
            (docs_profile or {}).get("detect", {}).get("capabilities_any", [])
        )
        if docs_profile and docs_markers & repo_caps:
            selected = ["docs-first-product"]
            provenance["docs-first-product"] = ["repository_evidence"]
        else:
            requires_confirmation = True
            warnings.append(
                "no project-family evidence or approved capabilities; profile selection is blocked"
            )

    for left in selected:
        allowed = set(profiles[left].get("composition", {}).get("compatible_with", []))
        for right in selected:
            if left == right:
                continue
            if allowed and right not in allowed:
                raise ContractError(
                    f"profile composition not allowed by {left!r}: {right!r}"
                )

    return {
        "selected_profiles": selected,
        "repo_capabilities": sorted(repo_caps),
        "approved_capabilities": sorted(approved_caps),
        "selection_provenance": provenance,
        "requires_confirmation": requires_confirmation,
        "warnings": warnings,
    }


def _path_rule_matches(path: str, rule: str) -> bool:
    """Return whether a repository-relative path matches a machine path rule."""

    if not rule or any(character.isspace() for character in rule):
        return False
    if rule.startswith("/") or "\x00" in rule:
        return False
    rule_parts = Path(rule.rstrip("/")).parts
    if ".." in rule_parts:
        return False
    if any(marker in rule for marker in ("*", "?", "[")):
        candidates = {rule}
        if rule.startswith("**/"):
            candidates.add(rule[3:])
        return any(fnmatch.fnmatchcase(path, candidate) for candidate in candidates)
    if rule.endswith("/"):
        return path.startswith(rule)
    return path == rule


def artifact_forbidden_by_graph(
    graph: dict[str, Any],
    path: str,
    phase: dict[str, Any] | None = None,
) -> list[str]:
    """Return canonical global or phase-local forbidden rules matching a path."""

    rules = [str(rule) for rule in graph.get("global_forbidden_write_paths", [])]
    if phase is not None:
        rules.extend(str(rule) for rule in phase.get("forbidden_writes", []))
    return sorted({rule for rule in rules if _path_rule_matches(path, rule)})


def phase_is_applicable(
    phase: dict[str, Any],
    selected_profile_ids: Iterable[str],
    capabilities: Iterable[str] = (),
) -> bool:
    """Evaluate a phase's executable applicability clause."""

    applicability = phase.get("applicability", {})
    profiles = set(selected_profile_ids)
    capability_set = set(capabilities)
    profiles_any = set(applicability.get("profiles_any", []))
    capabilities_any = set(applicability.get("capabilities_any", []))
    return (not profiles_any or bool(profiles_any & profiles)) and (
        not capabilities_any or bool(capabilities_any & capability_set)
    )


def artifact_phase_id(
    graph: dict[str, Any],
    path: str,
    selected_profile_ids: Iterable[str],
    capabilities: Iterable[str] = (),
) -> str:
    """Resolve one artifact to the most specific applicable phase write rule.

    Specific path rules win over broader directory rules. Later phases break
    equally specific ties so handoff and readiness artifacts remain attributed
    to the phase that finalizes them.
    """

    profiles = tuple(selected_profile_ids)
    capability_values = tuple(capabilities)
    candidates: list[tuple[int, int, str]] = []
    for phase in graph.get("phases", []):
        if not phase_is_applicable(phase, profiles, capability_values):
            continue
        if artifact_forbidden_by_graph(graph, path, phase):
            continue
        for rule in phase.get("allowed_writes", []):
            if _path_rule_matches(path, str(rule)):
                normalized = str(rule).rstrip("/")
                candidates.append(
                    (len(normalized), int(phase["order"]), str(phase["id"]))
                )
    if not candidates:
        raise ContractError(
            f"artifact path {path!r} is outside every applicable phase write boundary"
        )
    return max(candidates)[2]


def validate_artifact_phase(
    graph: dict[str, Any],
    *,
    path: str,
    phase_id: str,
    selected_profile_ids: Iterable[str],
    capabilities: Iterable[str] = (),
) -> None:
    """Fail unless the canonical graph authorizes a phase/path attribution."""

    phases = {
        str(phase["id"]): phase
        for phase in graph.get("phases", [])
        if isinstance(phase, dict) and "id" in phase
    }
    phase = phases.get(phase_id)
    if phase is None:
        raise ContractError(f"artifact {path!r} references unknown phase {phase_id!r}")
    if not phase_is_applicable(phase, selected_profile_ids, capabilities):
        raise ContractError(
            f"artifact {path!r} references inapplicable phase {phase_id!r}"
        )
    if not any(
        _path_rule_matches(path, str(rule))
        for rule in phase.get("allowed_writes", [])
    ):
        raise ContractError(
            f"artifact {path!r} is not allowed by phase {phase_id!r}"
        )
    forbidden = artifact_forbidden_by_graph(graph, path, phase)
    if forbidden:
        raise ContractError(
            f"artifact {path!r} is forbidden in phase {phase_id!r} by {forbidden}"
        )


def selected_artifacts(
    graph: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    selected_profile_ids: Iterable[str],
) -> dict[str, Any]:
    selected_ids = tuple(selected_profile_ids)
    required: dict[str, dict[str, Any]] = {}
    for item in graph.get("base_artifacts", []):
        artifact = dict(item)
        artifact["profiles"] = []
        required[item["path"]] = artifact
    optional: set[str] = set()
    forbidden: set[str] = set()
    for profile_id in selected_ids:
        profile = profiles[profile_id]
        for path in profile.get("artifacts", {}).get("required", []):
            artifact = required.setdefault(
                path,
                {
                    "path": path,
                    "source": f"templates/{path}",
                    "required": True,
                    "render": "copy",
                    "profiles": [],
                },
            )
            artifact_profiles = artifact.setdefault("profiles", [])
            if profile_id not in artifact_profiles:
                artifact_profiles.append(profile_id)
        optional.update(profile.get("artifacts", {}).get("optional", []))
        forbidden.update(profile.get("artifacts", {}).get("forbidden", []))
    # Profile forbiddance is a standalone negative assertion. During an approved
    # composition, an exact required path from any selected profile wins.
    forbidden.difference_update(required)
    for path, artifact in required.items():
        artifact["profiles"] = sorted(set(artifact.get("profiles", [])))
        artifact["phase_id"] = artifact_phase_id(graph, path, selected_ids)
    return {
        "required": [required[path] for path in sorted(required)],
        "optional": sorted(optional - set(required)),
        "forbidden": sorted(forbidden),
    }


def _bullet_lines(items: Iterable[str]) -> list[str]:
    values = [str(item) for item in items]
    return [f"- {item}" for item in values] if values else ["- None."]


def render_prompt(
    contract: dict[str, Any],
    source_rel: str = CONTRACT_REL.as_posix(),
    global_forbidden_write_paths: Iterable[str] = (),
) -> str:
    forbidden_writes = [
        *contract["forbidden_writes"],
        *(
            f"Machine-enforced global path rule: {rule}"
            for rule in global_forbidden_write_paths
        ),
    ]
    sections = [
        ("Goal", [contract["goal"]]),
        ("Context and required reads", contract["required_reads"]),
        ("Entry criteria", contract["entry_criteria"]),
        ("Constraints", contract["constraints"]),
        ("Allowed writes", contract["allowed_writes"]),
        ("Forbidden writes", forbidden_writes),
        ("Expected outputs", contract["expected_outputs"]),
        ("Evidence and checks", contract["evidence_and_checks"]),
        ("Stop or block when", contract["stop_conditions"]),
        ("Done when", contract["done_when"]),
        ("Runtime implementation boundary", [contract["runtime_boundary"]]),
    ]
    lines = [
        f"# Prompt: {contract['title']}",
        "",
        f"<!-- Generated from {source_rel}::{contract['id']}. Do not edit by hand. -->",
        "",
        "Use the `zero-to-hero` skill and follow this contract exactly.",
        "",
    ]
    applicability = contract.get("applicability")
    if applicability:
        lines.extend(["## Applicability", ""])
        for key, values in applicability.items():
            lines.append(f"- {key}: {', '.join(values)}")
        lines.append("")
    for heading, items in sections:
        lines.extend([f"## {heading}", "", *_bullet_lines(items), ""])
    return "\n".join(lines).rstrip() + "\n"


def rendered_prompt_files(graph: dict[str, Any]) -> dict[Path, bytes]:
    return {
        Path("prompts") / contract["prompt_file"]: render_prompt(
            contract,
            global_forbidden_write_paths=graph["global_forbidden_write_paths"],
        ).encode("utf-8")
        for contract in graph_prompts(graph)
    }


def rendered_phase_views(graph: dict[str, Any]) -> dict[Path, bytes]:
    phases = graph["phases"]
    state = {
        "schema_version": graph["schema_version"],
        "source": CONTRACT_REL.as_posix(),
        "global_forbidden_write_paths": graph["global_forbidden_write_paths"],
        "phases": [
            {
                "id": phase["id"],
                "order": phase["order"],
                "title": phase["title"],
                "prompt_file": phase["prompt_file"],
                "applicability": phase.get("applicability", {}),
                "entry_criteria": phase["entry_criteria"],
                "allowed_writes": phase["allowed_writes"],
                "forbidden_writes": phase["forbidden_writes"],
                "stop_conditions": phase["stop_conditions"],
                "done_when": phase["done_when"],
            }
            for phase in phases
        ],
    }
    gates = {
        "schema_version": graph["schema_version"],
        "source": CONTRACT_REL.as_posix(),
        "gates": {
            phase["id"]: {
                "entry": phase["entry_criteria"],
                "evidence": phase["evidence_and_checks"],
                "exit": phase["done_when"],
                "stop": phase["stop_conditions"],
            }
            for phase in phases
        },
    }
    artifacts = {
        "schema_version": graph["schema_version"],
        "source": CONTRACT_REL.as_posix(),
        "global_forbidden_write_paths": graph["global_forbidden_write_paths"],
        "phases": {
            phase["id"]: {
                "allowed_writes": phase["allowed_writes"],
                "forbidden_writes": phase["forbidden_writes"],
                "expected_outputs": phase["expected_outputs"],
            }
            for phase in phases
        },
    }
    return {
        Path("references/phase-state-machine.yaml"): (
            json.dumps(state, indent=2, sort_keys=False) + "\n"
        ).encode("utf-8"),
        Path("references/phase-gates.yaml"): (
            json.dumps(gates, indent=2, sort_keys=False) + "\n"
        ).encode("utf-8"),
        Path("references/phase-output-artifacts.yaml"): (
            json.dumps(artifacts, indent=2, sort_keys=False) + "\n"
        ).encode("utf-8"),
    }


def rendered_contract_views(graph: dict[str, Any]) -> dict[Path, bytes]:
    return {**rendered_phase_views(graph), **rendered_prompt_files(graph)}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
