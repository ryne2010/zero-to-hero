#!/usr/bin/env python3
"""Fail-closed, profile-aware audit of a generated zero-to-hero target repo."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_zero_to_hero_templates import (  # noqa: E402
    CANONICAL_MANIFEST,
    CANONICAL_MANIFEST_REL,
    GenerationError,
    _is_substantive,
    _load_approved_capabilities,
    _normalize_profile_args,
    _run_json_child,
    _sha256_path,
    _validate_agents_contract,
    validate_manifest,
)
from profile_evidence import evaluate_profile_evidence  # noqa: E402
from zero_to_hero_contract import (  # noqa: E402
    ContractError,
    load_graph,
    load_profiles,
    resolve_profiles,
    selected_artifacts,
    validate_capability_tokens,
)


def _child_result(script: Path, repo: Path, timeout: int = 30) -> dict[str, Any]:
    try:
        return {"ok": True, "report": _run_json_child(script, repo, timeout=timeout)}
    except GenerationError as exc:
        return {"ok": False, "error": str(exc)}


def _load_manifest(repo: Path) -> tuple[dict[str, Any] | None, list[str]]:
    path = repo / CANONICAL_MANIFEST
    failures: list[str] = []
    if not path.is_file() or path.is_symlink():
        return None, [f"missing canonical generated manifest: {CANONICAL_MANIFEST}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise GenerationError("manifest root is not an object")
        validate_manifest(data)
    except (OSError, json.JSONDecodeError, GenerationError) as exc:
        return None, [f"invalid canonical generated manifest: {exc}"]
    if data.get("status") != "complete":
        failures.append("canonical generated manifest is not marked complete")
    return data, failures


def _resolve_audit_profiles(
    *,
    skill: Path,
    capability_report: dict[str, Any],
    explicit_profiles: Iterable[str],
    approved_capabilities: Iterable[str],
    manifest: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    try:
        graph = load_graph(skill)
        profiles = load_profiles(skill)
    except ContractError as exc:
        return None, None, [f"cannot load executable contracts: {exc}"]
    explicit = list(explicit_profiles)
    if not explicit and manifest is not None:
        manifest_profiles = manifest.get("selected_profiles", [])
        if isinstance(manifest_profiles, list) and all(
            isinstance(item, str) for item in manifest_profiles
        ):
            explicit = manifest_profiles
    try:
        resolution = resolve_profiles(
            profiles,
            repo_capabilities=capability_report.get("capabilities", []),
            approved_capabilities=approved_capabilities,
            explicit_profiles=explicit,
        )
    except ContractError as exc:
        return graph, None, [f"profile resolution failed: {exc}"]
    if resolution.get("requires_confirmation") or not resolution.get("selected_profiles"):
        failures.append("profile selection remains unresolved")
    if manifest is not None and set(manifest.get("selected_profiles", [])) != set(
        resolution.get("selected_profiles", [])
    ):
        failures.append(
            "manifest selected_profiles do not match the audited profile composition"
        )
    resolution["artifacts"] = selected_artifacts(
        graph, profiles, resolution.get("selected_profiles", [])
    )
    resolution["profile_definitions"] = profiles
    return graph, resolution, failures


def _audit_required_artifacts(
    repo: Path, resolution: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for artifact in resolution["artifacts"]["required"]:
        rel = artifact["path"]
        path = repo / rel
        result: dict[str, Any] = {
            "target_path": rel,
            "source": artifact["source"],
            "exists": path.is_file() and not path.is_symlink(),
            "substantive": False,
        }
        if not result["exists"]:
            result["reason"] = "missing or not a regular file"
            failures.append(f"missing required artifact: {rel}")
        else:
            substantive, reason = _is_substantive(rel, path.read_bytes())
            result["substantive"] = substantive
            result["reason"] = reason
            result["sha256"] = _sha256_path(path)
            if not substantive:
                failures.append(f"non-substantive required artifact: {rel}: {reason}")
            if rel == "AGENTS.md" and substantive:
                selected_profiles = resolution["selected_profiles"]
                valid_agents, agents_reason = _validate_agents_contract(
                    repo,
                    path.read_bytes(),
                    selected_profiles=selected_profiles,
                    profile_required_paths={
                        profile_id: resolution["profile_definitions"][profile_id][
                            "artifacts"
                        ]["required"]
                        for profile_id in selected_profiles
                    },
                )
                result["target_specific"] = valid_agents
                result["agents_contract"] = agents_reason
                if not valid_agents:
                    failures.append(
                        f"AGENTS.md is not target-specific: {agents_reason}"
                    )
        results.append(result)
    return results, failures


def _audit_forbidden_artifacts(
    repo: Path, resolution: dict[str, Any]
) -> tuple[list[str], list[str]]:
    present = [
        path
        for path in resolution["artifacts"]["forbidden"]
        if (repo / path).exists()
    ]
    return present, [f"forbidden artifact is present: {path}" for path in present]


def _audit_profile_evidence(
    repo: Path, resolution: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    def read_artifact(rel: str) -> bytes | None:
        path = repo / rel
        if not path.is_file() or path.is_symlink():
            return None
        return path.read_bytes()

    return evaluate_profile_evidence(
        profiles=resolution["profile_definitions"],
        selected_profiles=resolution["selected_profiles"],
        read_artifact=read_artifact,
        substantive_check=_is_substantive,
    )


def _audit_manifest_records(
    repo: Path,
    manifest: dict[str, Any] | None,
    resolution: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    if manifest is None or resolution is None:
        return [], []
    failures: list[str] = []
    results: list[dict[str, Any]] = []
    records = {
        item["target_path"]: item
        for item in manifest.get("files", [])
        if isinstance(item, dict) and isinstance(item.get("target_path"), str)
    }
    required_paths = {item["path"] for item in resolution["artifacts"]["required"]}
    for rel in sorted(required_paths):
        record = records.get(rel)
        if record is None:
            failures.append(f"manifest has no record for required artifact: {rel}")
            continue
        actual = _sha256_path(repo / rel)
        expected = record.get("post_write_sha256")
        self_reference = rel == CANONICAL_MANIFEST_REL
        matches = self_reference and expected is None or actual == expected
        result = {
            "target_path": rel,
            "actual_sha256": actual,
            "manifest_sha256": expected,
            "self_reference": self_reference,
            "matches": matches,
        }
        results.append(result)
        if not matches:
            failures.append(f"manifest hash does not match required artifact: {rel}")
    unknown = sorted(set(records) - required_paths)
    if unknown:
        failures.append(
            "manifest records artifacts outside the audited required set: "
            + ", ".join(unknown)
        )
    return results, failures


def _report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Target repository audit",
        "",
        f"Repository: `{report['repo']}`",
        "",
        f"Result: **{report['status'].upper()}**",
        "",
        "## Selected profiles",
        "",
    ]
    lines.extend(
        f"- {profile}" for profile in report.get("selected_profiles", [])
    )
    if not report.get("selected_profiles"):
        lines.append("- none")
    lines.extend(["", "## Blocking failures", ""])
    lines.extend(f"- {item}" for item in report.get("failures", []))
    if not report.get("failures"):
        lines.append("- none")
    lines.extend(["", "## Required artifacts", ""])
    for item in report.get("required_artifacts", []):
        state = "pass" if item.get("exists") and item.get("substantive") else "fail"
        lines.append(f"- [{state}] `{item['target_path']}` — {item.get('reason')}")
    lines.extend(["", "## Child validations", ""])
    for name, result in report.get("child_validations", {}).items():
        lines.append(f"- {name}: {'pass' if result.get('ok') else 'fail'}")
    return "\n".join(lines).rstrip() + "\n"


def audit_target(
    *,
    repo: Path,
    skill: Path,
    explicit_profiles: Iterable[str] = (),
    approved_capabilities: Iterable[str] = (),
    mode: str = "post-generation",
) -> dict[str, Any]:
    if mode not in {"preflight", "post-generation"}:
        raise GenerationError(f"unknown target audit mode: {mode}")
    approved_capabilities = validate_capability_tokens(
        skill,
        approved_capabilities,
        label="approved capability data",
    )
    scripts = skill / "scripts"
    children = {
        "capability_detection": _child_result(
            scripts / "capability_detect.py", repo
        ),
        "instruction_trust": _child_result(
            scripts / "instruction_trust_scan.py", repo
        ),
        "toolchain_preflight": _child_result(
            scripts / "toolchain_preflight.py", repo
        ),
        "external_context": _child_result(
            scripts / "external_context_inventory.py", repo
        ),
        "repo_safety": _child_result(
            scripts / "repo_safety_check.py", repo
        ),
    }
    operational_failures = [
        f"required child validation failed: {name}: {result.get('error')}"
        for name, result in children.items()
        if not result.get("ok")
    ]
    readiness_gaps: list[str] = []
    caps = children["capability_detection"].get(
        "report", {"capabilities": [], "evidence": {}, "negative_evidence": {}}
    )
    manifest, manifest_failures = _load_manifest(repo)
    readiness_gaps.extend(manifest_failures)
    _, resolution, resolution_failures = _resolve_audit_profiles(
        skill=skill,
        capability_report=caps,
        explicit_profiles=explicit_profiles,
        approved_capabilities=approved_capabilities,
        manifest=manifest,
    )
    for failure in resolution_failures:
        if failure.startswith("cannot load executable contracts"):
            operational_failures.append(failure)
        else:
            readiness_gaps.append(failure)

    required_results: list[dict[str, Any]] = []
    forbidden_present: list[str] = []
    evidence_results: list[dict[str, Any]] = []
    manifest_results: list[dict[str, Any]] = []
    if resolution is not None:
        required_results, required_failures = _audit_required_artifacts(repo, resolution)
        forbidden_present, forbidden_failures = _audit_forbidden_artifacts(repo, resolution)
        evidence_results, evidence_failures = _audit_profile_evidence(repo, resolution)
        manifest_results, record_failures = _audit_manifest_records(
            repo, manifest, resolution
        )
        readiness_gaps.extend(required_failures)
        readiness_gaps.extend(forbidden_failures)
        readiness_gaps.extend(evidence_failures)
        readiness_gaps.extend(record_failures)

    trust = children["instruction_trust"].get("report", {})
    if children["instruction_trust"].get("ok"):
        if trust.get("truncated") or trust.get("skipped_large_files", 0):
            operational_failures.append(
                "instruction-trust scan was incomplete "
                f"(truncated={bool(trust.get('truncated'))}, "
                f"skipped_large_files={trust.get('skipped_large_files', 0)})"
            )
        if (
            trust.get("severity") not in {"none", None}
            or trust.get("finding_count", 0)
        ):
            readiness_gaps.append(
                "instruction-trust findings remain unresolved "
                f"(severity={trust.get('severity')}, count={trust.get('finding_count')})"
            )
    safety_report = children["repo_safety"].get("report", {})
    if children["repo_safety"].get("ok") and safety_report.get("git_status_error"):
        operational_failures.append(
            "repository safety status is indeterminate: "
            f"{safety_report['git_status_error']}"
        )
    operational_failures = list(dict.fromkeys(operational_failures))
    readiness_gaps = list(dict.fromkeys(readiness_gaps))
    failures = [*operational_failures, *readiness_gaps]
    ready = not failures
    if operational_failures:
        status = "failed"
    elif mode == "preflight":
        status = "preflight_complete"
    else:
        status = "passed" if ready else "failed"
    report = {
        "schema_version": 1,
        "tool": "zero-to-hero-target-repo-audit",
        "repo": str(repo),
        "mode": mode,
        "status": status,
        "ready": ready,
        "selected_profiles": (
            resolution.get("selected_profiles", []) if resolution is not None else []
        ),
        "repo_capabilities": caps.get("capabilities", []),
        "approved_capabilities": sorted(set(approved_capabilities)),
        "required_artifacts": required_results,
        "forbidden_artifacts_present": forbidden_present,
        "profile_evidence": evidence_results,
        "manifest_records": manifest_results,
        "child_validations": children,
        "operational_failures": operational_failures,
        "readiness_gaps": readiness_gaps,
        "failures": failures,
        "recommended_next_actions": [
            "resolve every blocking failure and rerun this audit"
        ]
        if failures
        else ["proceed only within the approved implementation handoff"],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a fail-closed, profile-aware zero-to-hero target audit."
    )
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument(
        "--profile",
        action="append",
        help="expected output profile; repeat or comma-separate for composition",
    )
    parser.add_argument(
        "--approved-capabilities-file",
        help="JSON discovery artifact containing approved capabilities",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write JSON and Markdown reports under .codex/reports/zero-to-hero",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help=(
            "inspect before generation; missing generated artifacts remain readiness gaps "
            "but do not make a successfully completed inspection exit nonzero"
        ),
    )
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    skill = Path(__file__).resolve().parents[1]
    approved_file = None
    if args.approved_capabilities_file:
        candidate = Path(args.approved_capabilities_file).expanduser()
        approved_file = (candidate if candidate.is_absolute() else repo / candidate).resolve()
    try:
        approved, _ = _load_approved_capabilities(approved_file, skill)
        profiles = _normalize_profile_args(args.profile)
        report = audit_target(
            repo=repo,
            skill=skill,
            explicit_profiles=profiles,
            approved_capabilities=approved,
            mode="preflight" if args.preflight else "post-generation",
        )
    except (GenerationError, ContractError) as exc:
        report = {
            "schema_version": 1,
            "tool": "zero-to-hero-target-repo-audit",
            "repo": str(repo),
            "mode": "preflight" if args.preflight else "post-generation",
            "status": "failed",
            "ready": False,
            "operational_failures": [str(exc)],
            "readiness_gaps": [],
            "failures": [str(exc)],
        }
    if args.write:
        outdir = repo / ".codex/reports/zero-to-hero"
        outdir.mkdir(parents=True, exist_ok=True)
        json_path = outdir / "target-repo-audit.json"
        md_path = outdir / "target-repo-audit.md"
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(_report_markdown(report), encoding="utf-8")
        report["written_reports"] = [str(json_path), str(md_path)]
    print(json.dumps(report, indent=2))
    if args.preflight and not report.get("operational_failures"):
        return 0
    return 0 if report.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
