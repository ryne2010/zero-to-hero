#!/usr/bin/env python3
"""Execute deterministic evidence checks declared by output profiles."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Iterable

ArtifactReader = Callable[[str], bytes | None]
SubstanceCheck = Callable[[str, bytes], tuple[bool, str]]

CHECK_PREFIXES = {"content", "review", "validation"}
CHECK_TOKEN_ALIASES: dict[str, tuple[str, ...]] = {
    "authz": ("authz", "authorization", "unauthorized"),
    "e2e": ("e2e", "end to end"),
    "eval": ("eval", "evaluation"),
    "filesystem": ("filesystem", "file system"),
    "ids": ("ids", "identifiers"),
    "io": ("io", "input output"),
}
IGNORED_CHECK_TOKENS = {"and", "or", "no"}
MIN_EVIDENCE_WORDS = 60
MIN_UNIQUE_EVIDENCE_WORDS = 30
MIN_CONTRACT_STATEMENTS = 3


def _normalized_text(data: bytes) -> str:
    text = data.decode("utf-8", errors="ignore").lower()
    return re.sub(r"[^a-z0-9+]+", " ", text).strip()


def _token_forms(token: str) -> set[str]:
    forms = {token}
    if token.endswith("ies") and len(token) > 4:
        forms.add(token[:-3] + "y")
    if token.endswith("es") and len(token) > 4:
        forms.add(token[:-2])
    if token.endswith("s") and len(token) > 3:
        forms.add(token[:-1])
    forms.update(CHECK_TOKEN_ALIASES.get(token, ()))
    return forms


def _token_matches(token: str, normalized: str, words: set[str]) -> bool:
    for form in _token_forms(token):
        if " " in form:
            if form in normalized:
                return True
        elif form in words:
            return True
    return False


def _evidence_depth(artifacts: dict[str, bytes]) -> dict[str, Any]:
    decoded = [
        data.decode("utf-8", errors="ignore") for data in artifacts.values()
    ]
    words = re.findall(r"[a-z0-9]+", "\n".join(decoded).lower())
    statements = []
    for text in decoded:
        for line in text.splitlines():
            candidate = line.strip().lstrip("-*0123456789. ").strip()
            if not candidate or candidate.startswith(("#", "|", "```")):
                continue
            if len(re.findall(r"[A-Za-z0-9]+", candidate)) >= 8:
                statements.append(candidate)
    return {
        "word_count": len(words),
        "unique_word_count": len(set(words)),
        "contract_statement_count": len(statements),
        "passed": (
            len(words) >= MIN_EVIDENCE_WORDS
            and len(set(words)) >= MIN_UNIQUE_EVIDENCE_WORDS
            and len(statements) >= MIN_CONTRACT_STATEMENTS
        ),
    }


def _content_check(check_id: str, artifacts: dict[str, bytes]) -> dict[str, Any]:
    _, slug = check_id.split(":", 1)
    tokens = [
        token
        for token in re.split(r"[-._]+", slug)
        if token and token not in IGNORED_CHECK_TOKENS
    ]
    normalized = " ".join(_normalized_text(data) for data in artifacts.values())
    words = set(normalized.split())
    matched = [token for token in tokens if _token_matches(token, normalized, words)]
    required_matches = len(tokens)
    depth = _evidence_depth(artifacts)
    passed = bool(tokens) and len(matched) == required_matches and depth["passed"]
    return {
        "id": check_id,
        "passed": passed,
        "kind": check_id.split(":", 1)[0],
        "matched_terms": matched,
        "required_term_matches": required_matches,
        "evidence_depth": depth,
        "artifacts_checked": sorted(artifacts),
        "detail": (
            f"matched {len(matched)} of {len(tokens)} declared semantic terms; "
            f"depth words={depth['word_count']}, unique={depth['unique_word_count']}, "
            f"statements={depth['contract_statement_count']}"
            if tokens
            else "check identifier has no semantic terms"
        ),
    }


def _dimension_ledger_check(
    check_id: str, artifacts: dict[str, bytes]
) -> dict[str, Any]:
    candidates = {
        path: data
        for path, data in artifacts.items()
        if Path(path).suffix.lower() in {".yaml", ".yml"}
    }
    required_types: dict[str, type] = {
        "units": dict,
        "coordinate_system": dict,
        "general_tolerances": dict,
        "dimensions": list,
        "fits": list,
        "tolerance_stacks": list,
        "unit_conversions": list,
        "validation_targets": list,
        "unresolved": list,
    }
    errors: list[str] = []
    try:
        import yaml
    except ImportError as exc:
        return {
            "id": check_id,
            "passed": False,
            "kind": "validation",
            "artifacts_checked": sorted(candidates),
            "detail": f"PyYAML is required for ledger validation: {exc}",
        }
    for path, data in candidates.items():
        try:
            value = yaml.safe_load(data.decode("utf-8"))
        except Exception as exc:
            errors.append(f"{path}: invalid YAML: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path}: root must be a mapping")
            continue
        if value.get("schema_version") != 1:
            errors.append(f"{path}: schema_version must be 1")
        for key, expected_type in required_types.items():
            if not isinstance(value.get(key), expected_type):
                errors.append(
                    f"{path}: {key} must be {expected_type.__name__}"
                )
        dimensions = value.get("dimensions")
        if isinstance(dimensions, list) and dimensions:
            first = dimensions[0]
            required_dimension_fields = {
                "id",
                "nominal",
                "unit",
                "tolerance",
                "validation_target",
            }
            if not isinstance(first, dict):
                errors.append(f"{path}: dimensions entries must be mappings")
            else:
                missing = sorted(required_dimension_fields - set(first))
                if missing:
                    errors.append(
                        f"{path}: first dimensions entry is missing {missing}"
                    )
    passed = bool(candidates) and not errors
    return {
        "id": check_id,
        "passed": passed,
        "kind": "validation",
        "artifacts_checked": sorted(candidates),
        "detail": (
            "dimension ledger parsed and required structural fields are present"
            if passed
            else "; ".join(errors) or "no YAML ledger candidate was available"
        ),
    }


def execute_check(check_id: str, artifacts: dict[str, bytes]) -> dict[str, Any]:
    if ":" not in check_id:
        return {
            "id": check_id,
            "passed": False,
            "kind": "unknown",
            "artifacts_checked": sorted(artifacts),
            "detail": "check id has no executable prefix",
        }
    prefix = check_id.split(":", 1)[0]
    if prefix not in CHECK_PREFIXES:
        return {
            "id": check_id,
            "passed": False,
            "kind": prefix,
            "artifacts_checked": sorted(artifacts),
            "detail": f"unsupported evidence check prefix: {prefix}",
        }
    if check_id == "validation:dimension-ledger-schema":
        return _dimension_ledger_check(check_id, artifacts)
    if prefix == "validation":
        return {
            "id": check_id,
            "passed": False,
            "kind": prefix,
            "artifacts_checked": sorted(artifacts),
            "detail": "validation check has no executable implementation",
        }
    return _content_check(check_id, artifacts)


def evaluate_profile_evidence(
    *,
    profiles: dict[str, dict[str, Any]],
    selected_profiles: Iterable[str],
    read_artifact: ArtifactReader,
    substantive_check: SubstanceCheck,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Evaluate each selected profile's artifacts and executable checks."""

    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for profile_id in selected_profiles:
        for requirement in profiles[profile_id].get("evidence_requirements", []):
            candidates = requirement.get("artifacts_any", [])
            substantive_artifacts: dict[str, bytes] = {}
            artifact_results: list[dict[str, Any]] = []
            for rel in candidates:
                data = read_artifact(rel)
                if data is None:
                    artifact_results.append(
                        {
                            "target_path": rel,
                            "substantive": False,
                            "reason": "missing or not a regular file",
                        }
                    )
                    continue
                substantive, reason = substantive_check(rel, data)
                artifact_results.append(
                    {
                        "target_path": rel,
                        "substantive": substantive,
                        "reason": reason,
                    }
                )
                if substantive:
                    substantive_artifacts[rel] = data

            declared_checks = requirement.get("checks_all", [])
            check_results = [
                execute_check(check_id, substantive_artifacts)
                for check_id in declared_checks
            ]
            passed_checks = [
                item["id"] for item in check_results if item.get("passed")
            ]
            failed_checks = [
                item["id"] for item in check_results if not item.get("passed")
            ]
            satisfied = (
                bool(substantive_artifacts)
                and bool(declared_checks)
                and not failed_checks
            )
            result = {
                "profile": profile_id,
                "id": requirement.get("id"),
                "description": requirement.get("description"),
                "artifacts_any": candidates,
                "artifact_results": artifact_results,
                "substantive_artifacts": sorted(substantive_artifacts),
                "checks_declared": declared_checks,
                "check_results": check_results,
                "passed_checks": passed_checks,
                "failed_checks": failed_checks,
                "satisfied": satisfied,
            }
            results.append(result)
            if not substantive_artifacts:
                failures.append(
                    "profile evidence requirement has no substantive artifact: "
                    f"{profile_id}/{requirement.get('id')}"
                )
            elif failed_checks or not declared_checks:
                failures.append(
                    "profile evidence requirement has failing executable checks: "
                    f"{profile_id}/{requirement.get('id')}: "
                    f"{', '.join(failed_checks) or 'none declared'}"
                )
    return results, failures
