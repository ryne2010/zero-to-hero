#!/usr/bin/env python3
"""Validate template or populated Ralplan planning-evidence provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError as exc:
    raise SystemExit(
        "planning-evidence validator dependencies unavailable; "
        f"use the pinned repository environment: {exc}"
    ) from exc


START_MARKER = "<!-- RALPLAN_EVIDENCE:START -->"
END_MARKER = "<!-- RALPLAN_EVIDENCE:END -->"
SCHEMA_NAME = "planning-evidence.schema.json"
TEMPLATE_RELATIVE = Path("templates/docs/implementation/PLANNING_EVIDENCE.md")
PROJECT_RELATIVE = Path("docs/implementation/PLANNING_EVIDENCE.md")
TRACKER_RELATIVE = ".omx/state/subagent-tracking.json"
SESSION_RELATIVE = ".omx/state/session.json"
MODE_STATE_NAMES = (
    "ralplan-state.json",
    "autopilot-state.json",
    "pipeline-state.json",
)
RFC3339_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$"
)
OMX_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class PlanningEvidenceError(ValueError):
    """Raised when planning-evidence input cannot be parsed safely."""


@dataclass(frozen=True)
class ReviewCycleContext:
    """Current OMX mode-state facts used to bind review freshness."""

    current_cycles: tuple[int, ...]
    return_parent_cycles: tuple[int, ...]
    return_to_ralplan: bool


def _load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanningEvidenceError(f"{label} is unreadable or invalid JSON: {exc}") from exc


def _extract_evidence(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PlanningEvidenceError(f"planning evidence is unreadable: {path}: {exc}") from exc
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise PlanningEvidenceError(
            "planning evidence must contain exactly one RALPLAN_EVIDENCE marker pair"
        )
    start_index = text.index(START_MARKER)
    end_index = text.index(END_MARKER)
    if end_index <= start_index:
        raise PlanningEvidenceError("planning-evidence marker order is invalid")
    bounded = text[start_index + len(START_MARKER) : end_index]
    match = re.fullmatch(
        r"\s*```(?:yaml|yml)\s*\n(?P<body>.*?)\n```\s*",
        bounded,
        flags=re.DOTALL,
    )
    if not match:
        raise PlanningEvidenceError(
            "RALPLAN_EVIDENCE markers must contain exactly one fenced YAML object"
        )
    try:
        payload = yaml.safe_load(match.group("body"))
    except yaml.YAMLError as exc:
        raise PlanningEvidenceError(f"planning-evidence YAML is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise PlanningEvidenceError("planning-evidence YAML root must be an object")
    return payload


def _schema_errors(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        return [f"planning-evidence schema is invalid: {exc}"]
    validator = Draft202012Validator(schema)
    failures = sorted(
        validator.iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    errors: list[str] = []
    for failure in failures:
        location = "/".join(str(part) for part in failure.absolute_path) or "<root>"
        errors.append(f"schema:{location}: {failure.message}")
    return errors


def _resolve_mode_and_path(target: Path, requested_mode: str) -> tuple[str, Path, Path]:
    if target.is_file():
        evidence_path = target.resolve()
        inferred_mode = "template" if "templates" in evidence_path.parts else "project"
        mode = inferred_mode if requested_mode == "auto" else requested_mode
        if mode == "template":
            try:
                template_index = evidence_path.parts.index("templates")
            except ValueError as exc:
                raise PlanningEvidenceError(
                    "template mode requires a path below a templates directory"
                ) from exc
            root = Path(*evidence_path.parts[:template_index])
        else:
            if evidence_path.name != "PLANNING_EVIDENCE.md":
                raise PlanningEvidenceError(
                    "project evidence file must be named PLANNING_EVIDENCE.md"
                )
            root = evidence_path.parents[2]
        return mode, root.resolve(), evidence_path

    root = target.resolve()
    template_path = root / TEMPLATE_RELATIVE
    project_path = root / PROJECT_RELATIVE
    if requested_mode == "auto":
        if project_path.is_file():
            mode = "project"
        elif template_path.is_file():
            mode = "template"
        else:
            raise PlanningEvidenceError(
                f"cannot find {PROJECT_RELATIVE} or {TEMPLATE_RELATIVE} below {root}"
            )
    else:
        mode = requested_mode
    evidence_path = template_path if mode == "template" else project_path
    if not evidence_path.is_file():
        raise PlanningEvidenceError(f"{mode} planning evidence is missing: {evidence_path}")
    return mode, root, evidence_path


def _template_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "evidence_status": "pending",
        "review_cycle": 0,
        "planning_artifacts.draft_owner": "pending",
        "planning_artifacts.prd_sha256": "<pending>",
        "planning_artifacts.test_spec_sha256": "<pending>",
        "role_routing.status": "pending",
        "role_routing.surface": "pending",
        "role_routing.documented_leader_proof": False,
        "ralplan_consensus_gate.ralplan_architect_review.agent_role": "architect",
        "ralplan_consensus_gate.ralplan_architect_review.provenance_kind": ("native_subagent"),
        "ralplan_consensus_gate.ralplan_architect_review.verdict": "pending",
        "ralplan_consensus_gate.ralplan_architect_review.review_cycle": 0,
        "ralplan_consensus_gate.ralplan_architect_review.completed_at": "<pending>",
        "ralplan_consensus_gate.ralplan_critic_review.agent_role": "critic",
        "ralplan_consensus_gate.ralplan_critic_review.provenance_kind": ("native_subagent"),
        "ralplan_consensus_gate.ralplan_critic_review.verdict": "pending",
        "ralplan_consensus_gate.ralplan_critic_review.review_cycle": 0,
        "ralplan_consensus_gate.ralplan_critic_review.completed_at": "<pending>",
        "ralplan_consensus_gate.complete": False,
    }
    for dotted, wanted in expected.items():
        value: Any = payload
        for key in dotted.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        if value != wanted:
            errors.append(f"template:{dotted}: expected {wanted!r}, found {value!r}")
    gate = payload.get("ralplan_consensus_gate")
    for review_key in ("ralplan_architect_review", "ralplan_critic_review"):
        review = gate.get(review_key) if isinstance(gate, dict) else None
        if isinstance(review, dict) and review.get("tracker_path") != TRACKER_RELATIVE:
            errors.append(
                "template:ralplan_consensus_gate."
                f"{review_key}.tracker_path: expected {TRACKER_RELATIVE!r}"
            )
    return errors


def _parse_timestamp(value: Any, label: str, errors: list[str]) -> float | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty timestamp")
        return None
    normalized = value.strip()
    if not RFC3339_PATTERN.fullmatch(normalized):
        errors.append(f"{label} must be a timezone-bearing RFC 3339 timestamp: {value!r}")
        return None
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        errors.append(f"{label} is not a valid RFC 3339 timestamp: {value!r}")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{label} must include an explicit RFC 3339 timezone: {value!r}")
        return None
    return parsed.timestamp()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_repo_path(root: Path, relative: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative:
        errors.append(f"{label} must be a non-empty repository-relative path")
        return None
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        errors.append(f"{label} escapes the repository root: {relative!r}")
        return None
    return candidate


def _current_session_state(
    root: Path,
    errors: list[str],
) -> tuple[dict[str, Any] | None, Path]:
    session_path = root / SESSION_RELATIVE
    if not session_path.is_file():
        errors.append(f"session:missing {SESSION_RELATIVE}")
        return None, session_path
    try:
        state = _load_json(session_path, "current OMX session state")
    except PlanningEvidenceError as exc:
        errors.append(str(exc))
        return None, session_path
    if not isinstance(state, dict):
        errors.append("session:current OMX session state must be an object")
        return None, session_path
    session_id = state.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        errors.append("session:current OMX session_id is required")
    elif not OMX_SESSION_ID_PATTERN.fullmatch(session_id.strip()):
        errors.append("session:current OMX session_id is invalid")
    state_cwd = state.get("cwd")
    if isinstance(state_cwd, str) and state_cwd.strip():
        if Path(state_cwd).expanduser().resolve() != root:
            errors.append("session:current OMX session cwd does not match the target repository")
    return state, session_path


def _mode_review_cycle_context(
    root: Path,
    session_id: str,
    errors: list[str],
) -> ReviewCycleContext | None:
    state_root = root / ".omx/state"
    scoped_root = state_root / "sessions" / session_id
    scoped = [scoped_root / name for name in MODE_STATE_NAMES]
    unscoped = [state_root / name for name in MODE_STATE_NAMES]
    candidates = [path for path in scoped if path.is_file()]
    if not candidates:
        candidates = [path for path in unscoped if path.is_file()]
    if not candidates:
        errors.append(f"cycle:missing current OMX mode state for session {session_id!r}")
        return None

    cycles: list[int] = []
    return_parent_cycles: list[int] = []
    return_to_ralplan = False
    for path in candidates:
        try:
            state = _load_json(path, f"OMX mode state {path}")
        except PlanningEvidenceError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(state, dict):
            errors.append(f"cycle:{path} must contain an object")
            continue
        recorded_session = state.get("session_id")
        if (
            isinstance(recorded_session, str)
            and recorded_session.strip()
            and recorded_session.strip() != session_id
        ):
            errors.append(
                f"cycle:{path} belongs to session {recorded_session!r}, "
                f"not current session {session_id!r}"
            )
            continue
        for record in (state, state.get("state")):
            if not isinstance(record, dict):
                continue
            cycle: int | None = None
            if "review_cycle" in record:
                raw_cycle = record.get("review_cycle")
                if isinstance(raw_cycle, bool) or not isinstance(raw_cycle, int) or raw_cycle < 0:
                    errors.append(f"cycle:{path} review_cycle must be a non-negative integer")
                else:
                    cycle = raw_cycle
                    cycles.append(raw_cycle)

            current_phase = str(record.get("current_phase", "")).lower()
            return_reason = record.get("return_to_ralplan_reason")
            is_return = (
                current_phase == "ralplan"
                and isinstance(return_reason, str)
                and bool(return_reason.strip())
            )
            if not is_return:
                continue

            return_to_ralplan = True
            if "return_to_ralplan_parent_review_cycle" in record:
                raw_parent = record.get("return_to_ralplan_parent_review_cycle")
                if (
                    isinstance(raw_parent, bool)
                    or not isinstance(raw_parent, int)
                    or raw_parent < 0
                ):
                    errors.append(
                        f"cycle:{path} return_to_ralplan_parent_review_cycle "
                        "must be a non-negative integer"
                    )
                else:
                    return_parent_cycles.append(raw_parent)
            elif cycle is not None:
                # OMX 0.20.3 withParentReturnToRalplanContext uses the
                # returning mode's review_cycle as the parent cycle when the
                # explicit parent field is absent.
                return_parent_cycles.append(cycle)

    return ReviewCycleContext(
        current_cycles=tuple(cycles),
        return_parent_cycles=tuple(return_parent_cycles),
        return_to_ralplan=return_to_ralplan,
    )


def _validate_review_cycle_freshness(
    root: Path,
    session_id: str,
    evidence_cycle: int,
    errors: list[str],
) -> None:
    context = _mode_review_cycle_context(root, session_id, errors)
    if context is None:
        return

    if context.return_to_ralplan:
        if not context.return_parent_cycles:
            errors.append(
                "cycle:return-to-Ralplan mode state does not provide a parent review_cycle"
            )
            return
        parent_cycle = max(context.return_parent_cycles)
        if evidence_cycle <= parent_cycle:
            errors.append(
                f"cycle:evidence review_cycle {evidence_cycle} is stale for "
                "return-to-Ralplan; it must be greater than parent "
                f"review_cycle {parent_cycle}"
            )
            return

        # A current mode-state record may already persist the advanced
        # candidate cycle (for example beside an explicit parent cycle). When
        # it does, bind to that exact current value. Otherwise the evidence
        # itself is the OMX candidate and only the strict parent advance is
        # authoritative.
        advanced_cycles = [cycle for cycle in context.current_cycles if cycle > parent_cycle]
        if advanced_cycles and evidence_cycle != max(advanced_cycles):
            errors.append(
                f"cycle:evidence review_cycle {evidence_cycle} does not match "
                "the current advanced OMX review_cycle "
                f"{max(advanced_cycles)}"
            )
        return

    if context.current_cycles:
        current_cycle = max(context.current_cycles)
        if evidence_cycle != current_cycle:
            errors.append(
                f"cycle:evidence review_cycle {evidence_cycle} is stale; "
                f"current OMX review_cycle is {current_cycle}"
            )
        return

    # OMX 0.20.3 seeds standalone Ralplan state without review_cycle and
    # accepts the initial consensus outside a return loop. Bind that sole
    # absence case to cycle zero rather than accepting an ungrounded nonzero
    # cycle.
    if evidence_cycle != 0:
        errors.append(
            f"cycle:evidence review_cycle {evidence_cycle} is ungrounded; "
            "initial OMX Ralplan state without review_cycle binds only to "
            "review_cycle 0"
        )


def _project_errors(
    payload: dict[str, Any],
    root: Path,
) -> tuple[list[str], Path | None]:
    errors: list[str] = []
    if payload.get("evidence_status") != "complete":
        errors.append("project:evidence_status must be complete before execution handoff")

    role_routing = payload.get("role_routing")
    if not isinstance(role_routing, dict):
        errors.append("project:role_routing is missing")
        return errors, None
    if role_routing.get("status") != "available":
        reason = role_routing.get("blocked_reason")
        errors.append(
            "project:native agent_type role routing is unavailable"
            + (f": {reason}" if reason else "")
        )
    if role_routing.get("surface") != "native_agent_type":
        errors.append("project:role_routing.surface must be native_agent_type")
    if role_routing.get("documented_leader_proof") is not True:
        errors.append("project:documented native leader proof is required")

    evidence_cycle = payload.get("review_cycle")
    if (
        isinstance(evidence_cycle, bool)
        or not isinstance(evidence_cycle, int)
        or evidence_cycle < 0
    ):
        errors.append("project:review_cycle must be a non-negative integer")

    artifacts = payload.get("planning_artifacts")
    if isinstance(artifacts, dict):
        if artifacts.get("draft_owner") not in {"main", "planner"}:
            errors.append("project:draft_owner must be main or planner")
        for field, digest_field in (
            ("prd_path", "prd_sha256"),
            ("test_spec_path", "test_spec_sha256"),
        ):
            artifact_path = _safe_repo_path(
                root,
                artifacts.get(field),
                f"project:planning_artifacts.{field}",
                errors,
            )
            if artifact_path is not None and not artifact_path.is_file():
                errors.append(
                    f"project:planning_artifacts.{field} does not exist: {artifacts.get(field)}"
                )
            elif artifact_path is not None:
                try:
                    current_digest = _sha256_file(artifact_path)
                except OSError as exc:
                    errors.append(f"project:planning_artifacts.{field} is unreadable: {exc}")
                    continue
                recorded_digest = artifacts.get(digest_field)
                if current_digest != recorded_digest:
                    errors.append(
                        f"project:planning_artifacts.{digest_field} does not match "
                        f"the current {field} bytes"
                    )

    gate = payload.get("ralplan_consensus_gate")
    if not isinstance(gate, dict):
        errors.append("project:ralplan_consensus_gate is missing")
        return errors, None
    architect = gate.get("ralplan_architect_review")
    critic = gate.get("ralplan_critic_review")
    if not isinstance(architect, dict) or not isinstance(critic, dict):
        errors.append(
            "project:Architect and Critic review records must be nested inside "
            "ralplan_consensus_gate"
        )
        return errors, None
    review_completed: dict[str, float | None] = {}
    for label, review, expected_role in (
        ("architect", architect, "architect"),
        ("critic", critic, "critic"),
    ):
        if review.get("agent_role") != expected_role:
            errors.append(f"project:{label} review agent_role must be {expected_role}")
        if review.get("provenance_kind") != "native_subagent":
            errors.append(f"project:{label} review provenance_kind must be native_subagent")
        if review.get("verdict") != "approve":
            errors.append(f"project:{label} review verdict must be approve")
        if review.get("tracker_path") != TRACKER_RELATIVE:
            errors.append(f"project:{label} review tracker_path must be {TRACKER_RELATIVE}")
        if review.get("review_cycle") != evidence_cycle:
            errors.append(
                f"cycle:{label} review_cycle must equal current evidence "
                f"review_cycle {evidence_cycle!r}"
            )
        review_completed[label] = _parse_timestamp(
            review.get("completed_at"),
            f"project:{label}.completed_at",
            errors,
        )

    if gate.get("complete") is not True:
        errors.append("project:ralplan_consensus_gate.complete must be true")

    architect_session = architect.get("session_id")
    critic_session = critic.get("session_id")
    if architect_session != critic_session:
        errors.append("tracker:Architect and Critic reviews must use the same session_id")
    session_state, _ = _current_session_state(root, errors)
    current_session_id = (
        session_state.get("session_id").strip()
        if isinstance(session_state, dict)
        and isinstance(session_state.get("session_id"), str)
        and session_state.get("session_id").strip()
        and OMX_SESSION_ID_PATTERN.fullmatch(session_state.get("session_id").strip())
        else ""
    )
    session_id = str(architect_session)
    if current_session_id and (
        architect_session != current_session_id or critic_session != current_session_id
    ):
        errors.append(
            "session:Architect and Critic evidence must belong to the current "
            f"OMX session {current_session_id!r}"
        )
    if current_session_id and isinstance(evidence_cycle, int):
        _validate_review_cycle_freshness(
            root,
            current_session_id,
            evidence_cycle,
            errors,
        )

    architect_thread_id = str(architect.get("thread_id"))
    critic_thread_id = str(critic.get("thread_id"))
    if architect_thread_id == critic_thread_id:
        errors.append("tracker:Architect and Critic reviews must use distinct thread_id values")

    tracker_path = _safe_repo_path(
        root,
        architect.get("tracker_path"),
        "tracker_path",
        errors,
    )
    if tracker_path is None:
        return errors, None
    if not tracker_path.is_file():
        errors.append(f"tracker:missing {TRACKER_RELATIVE}")
        return errors, tracker_path
    try:
        tracker = _load_json(tracker_path, "subagent tracker")
    except PlanningEvidenceError as exc:
        errors.append(str(exc))
        return errors, tracker_path
    if not isinstance(tracker, dict) or tracker.get("schemaVersion") != 1:
        errors.append("tracker:schemaVersion must be 1")
        return errors, tracker_path
    sessions = tracker.get("sessions")
    tracker_session_id = current_session_id or session_id
    session = sessions.get(tracker_session_id) if isinstance(sessions, dict) else None
    if not isinstance(session, dict):
        errors.append(f"tracker:session {tracker_session_id!r} is missing")
        return errors, tracker_path
    if session.get("session_id") != tracker_session_id:
        errors.append("tracker:session_id does not match the session map key")
    threads = session.get("threads")
    if not isinstance(threads, dict):
        errors.append(f"tracker:session {tracker_session_id!r} has no threads object")
        return errors, tracker_path
    raw_leader_thread_id = session.get("leader_thread_id")
    leader_thread_id = raw_leader_thread_id.strip() if isinstance(raw_leader_thread_id, str) else ""
    native_leader_thread_id = (
        session_state.get("native_session_id").strip()
        if isinstance(session_state, dict)
        and isinstance(session_state.get("native_session_id"), str)
        else ""
    )

    resolved: dict[str, tuple[dict[str, Any], float | None]] = {}
    for role, thread_id in (
        ("architect", architect_thread_id),
        ("critic", critic_thread_id),
    ):
        thread = threads.get(thread_id)
        if not isinstance(thread, dict):
            errors.append(f"tracker:{role} thread {thread_id!r} is missing")
            continue
        if thread_id in {leader_thread_id, native_leader_thread_id}:
            errors.append(f"tracker:{role} review thread is the current session leader")
        if thread.get("thread_id") != thread_id:
            errors.append(f"tracker:{role} thread_id does not match its map key")
        if thread.get("kind") != "subagent":
            errors.append(f"tracker:{role} thread kind must be subagent")
        provenance = thread.get("provenance_kind")
        if provenance not in {None, "", "native_subagent"}:
            errors.append(f"tracker:{role} thread provenance_kind conflicts with native_subagent")
        tracker_role = thread.get("role") or thread.get("mode")
        if tracker_role and tracker_role != role:
            errors.append(
                f"tracker:{role} thread role identity is {tracker_role!r}, expected {role!r}"
            )
        completed = _parse_timestamp(
            thread.get("completed_at"),
            f"tracker:{role}.completed_at",
            errors,
        )
        resolved[role] = (thread, completed)
        recorded_completed = review_completed.get(role)
        if (
            completed is not None
            and recorded_completed is not None
            and completed != recorded_completed
        ):
            errors.append(
                f"tracker:{role} review completed_at does not match the current tracker thread"
            )

    if "architect" in resolved and "critic" in resolved:
        architect_completed = resolved["architect"][1]
        critic_thread = resolved["critic"][0]
        critic_started_value = critic_thread.get("first_seen_at")
        critic_started_label = "first_seen_at"
        if critic_started_value is None:
            critic_started_value = critic_thread.get("started_at")
            critic_started_label = "started_at"
        critic_started = _parse_timestamp(
            critic_started_value,
            f"tracker:critic.{critic_started_label}",
            errors,
        )
        if (
            architect_completed is not None
            and critic_started is not None
            and architect_completed >= critic_started
        ):
            errors.append(
                "tracker:Architect completed_at must be strictly before "
                "Critic first_seen_at or started_at"
            )
    return errors, tracker_path


def check_planning_evidence(
    target: Path,
    *,
    mode: str = "auto",
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Return a deterministic validation report for a skill template or project."""

    errors: list[str] = []
    resolved_mode: str | None = None
    root: Path | None = None
    evidence_path: Path | None = None
    tracker_path: Path | None = None
    bundled_schema = Path(__file__).resolve().parents[1] / "schemas" / SCHEMA_NAME
    selected_schema = (schema_path or bundled_schema).resolve()
    try:
        resolved_mode, root, evidence_path = _resolve_mode_and_path(target, mode)
        schema = _load_json(selected_schema, "planning-evidence schema")
        if not isinstance(schema, dict):
            raise PlanningEvidenceError("planning-evidence schema root must be an object")
        payload = _extract_evidence(evidence_path)
        errors.extend(_schema_errors(payload, schema))
        if not errors:
            if resolved_mode == "template":
                errors.extend(_template_errors(payload))
            else:
                project_failures, tracker_path = _project_errors(payload, root)
                errors.extend(project_failures)
    except PlanningEvidenceError as exc:
        errors.append(str(exc))
    return {
        "status": "PASS" if not errors else "FAIL",
        "mode": resolved_mode or mode,
        "root": str(root) if root else str(target.resolve()),
        "evidence_path": str(evidence_path) if evidence_path else None,
        "schema_path": str(selected_schema),
        "tracker_path": str(tracker_path) if tracker_path else None,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument(
        "--mode",
        choices=("auto", "template", "project"),
        default="auto",
        help="validate the packaged pending template or a populated target project",
    )
    parser.add_argument("--schema", type=Path, help="override the bundled JSON schema")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = check_planning_evidence(
        Path(args.target),
        mode=args.mode,
        schema_path=args.schema,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif report["status"] == "PASS":
        print(f"planning evidence: PASS ({report['mode']} contract; {report['evidence_path']})")
    else:
        print(f"planning evidence: FAIL ({report['mode']} contract)")
        for error in report["errors"]:
            print(f"ERROR: {error}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
