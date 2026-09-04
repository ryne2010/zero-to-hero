#!/usr/bin/env python3
"""Hermetic contract tests for machine-verifiable Ralplan planning evidence."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import yaml

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import planning_evidence_check as checker  # noqa: E402


SKILL = Path(__file__).resolve().parents[1]
SCHEMA = SKILL / "schemas" / checker.SCHEMA_NAME
CHECKER = Path(checker.__file__).resolve()
PayloadMutator = Callable[[dict[str, Any]], None]
ARTIFACT_BYTES = b"# fixture\n"
ARTIFACT_SHA256 = hashlib.sha256(ARTIFACT_BYTES).hexdigest()
INITIAL_REVIEW_CYCLE = 0
RETURN_PARENT_CYCLE = 1
RETURN_REVIEW_CYCLE = 2


def _payload(
    owner: str = "main",
    review_cycle: int = INITIAL_REVIEW_CYCLE,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "evidence_status": "complete",
        "review_cycle": review_cycle,
        "planning_artifacts": {
            "draft_owner": owner,
            "prd_path": ".omx/plans/prd-demo.md",
            "prd_sha256": ARTIFACT_SHA256,
            "test_spec_path": ".omx/plans/test-spec-demo.md",
            "test_spec_sha256": ARTIFACT_SHA256,
        },
        "role_routing": {
            "status": "available",
            "surface": "native_agent_type",
            "documented_leader_proof": True,
            "blocked_reason": None,
        },
        "ralplan_consensus_gate": {
            "required": True,
            "sequence": ["architect-review", "critic-review"],
            "planning_artifacts_are_not_consensus": True,
            "required_review_roles": ["architect", "critic"],
            "ralplan_architect_review": {
                "agent_role": "architect",
                "provenance_kind": "native_subagent",
                "verdict": "approve",
                "review_cycle": review_cycle,
                "completed_at": "2026-07-23T10:00:00.000Z",
                "session_id": "sess-demo",
                "thread_id": "thread-architect",
                "tracker_path": checker.TRACKER_RELATIVE,
            },
            "ralplan_critic_review": {
                "agent_role": "critic",
                "provenance_kind": "native_subagent",
                "verdict": "approve",
                "review_cycle": review_cycle,
                "completed_at": "2026-07-23T10:05:00.000Z",
                "session_id": "sess-demo",
                "thread_id": "thread-critic",
                "tracker_path": checker.TRACKER_RELATIVE,
            },
            "complete": True,
            "blocked_reason": None,
        },
    }


def _tracker() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "sessions": {
            "sess-demo": {
                "session_id": "sess-demo",
                "leader_thread_id": "thread-leader",
                "updated_at": "2026-07-23T10:05:00.000Z",
                "threads": {
                    "thread-leader": {
                        "thread_id": "thread-leader",
                        "kind": "leader",
                        "first_seen_at": "2026-07-23T09:55:00.000Z",
                        "last_seen_at": "2026-07-23T10:05:00.000Z",
                        "turn_count": 3,
                    },
                    "thread-architect": {
                        "thread_id": "thread-architect",
                        "kind": "subagent",
                        "role": "architect",
                        "provenance_kind": "native_subagent",
                        "first_seen_at": "2026-07-23T09:58:00.000Z",
                        "last_seen_at": "2026-07-23T10:00:00.000Z",
                        "completed_at": "2026-07-23T10:00:00.000Z",
                        "turn_count": 1,
                    },
                    "thread-critic": {
                        "thread_id": "thread-critic",
                        "kind": "subagent",
                        "role": "critic",
                        "provenance_kind": "native_subagent",
                        "first_seen_at": "2026-07-23T10:01:00.000Z",
                        "last_seen_at": "2026-07-23T10:05:00.000Z",
                        "completed_at": "2026-07-23T10:05:00.000Z",
                        "turn_count": 1,
                    },
                },
            }
        },
        "pending_role_intents": [],
    }


def _write_evidence(path: Path, payload: dict[str, Any]) -> None:
    rendered = yaml.safe_dump(payload, sort_keys=False).rstrip()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Planning evidence\n\n"
        f"{checker.START_MARKER}\n"
        "```yaml\n"
        f"{rendered}\n"
        "```\n"
        f"{checker.END_MARKER}\n",
        encoding="utf-8",
    )


def _reviews(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    gate = payload["ralplan_consensus_gate"]
    return (
        gate["ralplan_architect_review"],
        gate["ralplan_critic_review"],
    )


def _project_report(
    payload_mutator: PayloadMutator | None = None,
    tracker_mutator: PayloadMutator | None = None,
    session_mutator: PayloadMutator | None = None,
    mode_state_mutator: PayloadMutator | None = None,
    *,
    owner: str = "main",
    review_cycle: int = INITIAL_REVIEW_CYCLE,
    write_tracker: bool = True,
    write_artifacts: bool = True,
    write_session: bool = True,
    write_mode_state: bool = True,
    artifact_bytes: bytes = ARTIFACT_BYTES,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="z2h-planning-evidence-") as temp:
        root = Path(temp)
        payload = _payload(owner, review_cycle)
        tracker = _tracker()
        session_state = {
            "session_id": "sess-demo",
            "native_session_id": "thread-leader",
            "cwd": str(root),
        }
        mode_state = {
            "active": True,
            "session_id": "sess-demo",
            "mode": "ralplan",
            "current_phase": "planning",
        }
        if payload_mutator:
            payload_mutator(payload)
        if tracker_mutator:
            tracker_mutator(tracker)
        if session_mutator:
            session_mutator(session_state)
        if mode_state_mutator:
            mode_state_mutator(mode_state)
        _write_evidence(root / checker.PROJECT_RELATIVE, payload)
        if write_artifacts:
            for relative in (
                ".omx/plans/prd-demo.md",
                ".omx/plans/test-spec-demo.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(artifact_bytes)
        if write_session:
            session_path = root / checker.SESSION_RELATIVE
            session_path.parent.mkdir(parents=True, exist_ok=True)
            session_path.write_text(
                json.dumps(session_state, indent=2) + "\n",
                encoding="utf-8",
            )
        if write_mode_state:
            mode_path = (
                root
                / ".omx/state/sessions"
                / str(session_state.get("session_id", "sess-demo"))
                / "ralplan-state.json"
            )
            mode_path.parent.mkdir(parents=True, exist_ok=True)
            mode_path.write_text(
                json.dumps(mode_state, indent=2) + "\n",
                encoding="utf-8",
            )
        if write_tracker:
            tracker_path = root / checker.TRACKER_RELATIVE
            tracker_path.parent.mkdir(parents=True, exist_ok=True)
            tracker_path.write_text(
                json.dumps(tracker, indent=2) + "\n",
                encoding="utf-8",
            )
        return checker.check_planning_evidence(
            root,
            mode="project",
            schema_path=SCHEMA,
        )


def _record(
    checks: list[dict[str, Any]],
    name: str,
    condition: bool,
    detail: Any,
) -> None:
    checks.append({"check": name, "ok": bool(condition), "detail": detail})


def _fails(report: dict[str, Any], fragment: str | None = None) -> bool:
    if report["status"] != "FAIL":
        return False
    if fragment is None:
        return True
    return fragment.lower() in " ".join(report["errors"]).lower()


def _installed_omx_package() -> Path | None:
    executable = shutil.which("omx")
    if not executable:
        return None
    resolved = Path(executable).resolve()
    for candidate in resolved.parents:
        package_json = candidate / "package.json"
        if candidate.name == "oh-my-codex" and package_json.is_file():
            return candidate
    return None


def _omx_0203_differential() -> dict[str, Any]:
    package = _installed_omx_package()
    node = shutil.which("node")
    if package is None or node is None:
        return {
            "status": "SKIP",
            "reason": "installed OMX or Node.js is unavailable",
        }
    package_metadata = json.loads((package / "package.json").read_text(encoding="utf-8"))
    version = package_metadata.get("version")
    if version != "0.20.3":
        return {
            "status": "SKIP",
            "reason": f"installed OMX version is {version!r}, not audited 0.20.3",
        }
    module_path = package / "dist/ralplan/consensus-gate.js"
    if not module_path.is_file():
        return {
            "status": "FAIL",
            "reason": f"installed OMX consensus module is missing: {module_path}",
        }

    initial = _payload()
    fresh_return = _payload(review_cycle=RETURN_REVIEW_CYCLE)
    fresh_return.update(
        {
            "current_phase": "ralplan",
            "return_to_ralplan_reason": "QA findings require plan revision",
            "return_to_ralplan_parent_review_cycle": RETURN_PARENT_CYCLE,
        }
    )
    stale_return = json.loads(json.dumps(fresh_return))
    _, stale_return_critic = _reviews(stale_return)
    stale_return_critic["review_cycle"] = RETURN_PARENT_CYCLE

    sibling = json.loads(json.dumps(initial))
    sibling_gate = sibling["ralplan_consensus_gate"]
    sibling["ralplan_architect_review"] = sibling_gate.pop("ralplan_architect_review")
    sibling["ralplan_critic_review"] = sibling_gate.pop("ralplan_critic_review")
    with tempfile.TemporaryDirectory(prefix="z2h-omx-ralplan-differential-") as temp:
        root = Path(temp).resolve()
        tracker_path = root / checker.TRACKER_RELATIVE
        tracker_path.parent.mkdir(parents=True, exist_ok=True)
        tracker_path.write_text(
            json.dumps(_tracker(), indent=2) + "\n",
            encoding="utf-8",
        )
        session_path = root / checker.SESSION_RELATIVE
        session_path.write_text(
            json.dumps(
                {
                    "session_id": "sess-demo",
                    "native_session_id": "thread-leader",
                    "cwd": str(root),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        node_script = """
import fs from "node:fs";
const input = JSON.parse(fs.readFileSync(0, "utf8"));
const module = await import(input.module_url);
const options = {
  cwd: input.cwd,
  sessionId: input.session_id,
  requireNativeSubagents: true,
};
const initial = module.buildRalplanConsensusGateFromSources(
  [{source: "zero-to-hero-initial", value: input.initial}],
  options,
);
const freshReturn = module.buildRalplanConsensusGateFromSources(
  [{source: "zero-to-hero-fresh-return", value: input.fresh_return}],
  options,
);
const staleReturn = module.buildRalplanConsensusGateFromSources(
  [{source: "zero-to-hero-stale-return", value: input.stale_return}],
  options,
);
const sibling = module.buildRalplanConsensusGateFromSources(
  [{source: "zero-to-hero-prior-sibling", value: input.sibling}],
  options,
);
process.stdout.write(JSON.stringify({initial, freshReturn, staleReturn, sibling}));
""".strip()
        env = os.environ.copy()
        env.pop("OMX_STATE_ROOT", None)
        completed = subprocess.run(
            [
                node,
                "--input-type=module",
                "--eval",
                node_script,
            ],
            input=json.dumps(
                {
                    "module_url": module_path.resolve().as_uri(),
                    "cwd": str(root),
                    "session_id": "sess-demo",
                    "initial": initial,
                    "fresh_return": fresh_return,
                    "stale_return": stale_return,
                    "sibling": sibling,
                }
            ),
            text=True,
            capture_output=True,
            check=False,
            env=env,
            timeout=30,
        )
    if completed.returncode != 0:
        return {
            "status": "FAIL",
            "reason": "installed OMX differential process failed",
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    try:
        output = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {
            "status": "FAIL",
            "reason": f"installed OMX differential emitted invalid JSON: {exc}",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    initial_gate = output.get("initial", {})
    fresh_return_gate = output.get("freshReturn", {})
    stale_return_gate = output.get("staleReturn", {})
    sibling_gate = output.get("sibling", {})
    return {
        "status": (
            "PASS"
            if initial_gate.get("complete") is True
            and fresh_return_gate.get("complete") is True
            and stale_return_gate.get("complete") is False
            and sibling_gate.get("complete") is False
            else "FAIL"
        ),
        "omx_version": version,
        "initial_without_mode_cycle": initial_gate,
        "fresh_return_cycle": fresh_return_gate,
        "stale_return_cycle": stale_return_gate,
        "prior_sibling": sibling_gate,
    }


def run_tests() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def return_mode_state(mode_state: dict[str, Any]) -> None:
        mode_state.update(
            {
                "current_phase": "ralplan",
                "review_cycle": RETURN_PARENT_CYCLE,
                "return_to_ralplan_reason": ("QA findings require a fresh consensus cycle"),
            }
        )

    template_report = checker.check_planning_evidence(
        SKILL,
        mode="template",
        schema_path=SCHEMA,
    )
    _record(
        checks,
        "source-template-contract",
        template_report["status"] == "PASS",
        template_report,
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            str(SKILL),
            "--mode",
            "template",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        cli_report = json.loads(completed.stdout)
    except json.JSONDecodeError:
        cli_report = {"status": "INVALID", "stdout": completed.stdout}
    _record(
        checks,
        "template-cli-json-contract",
        completed.returncode == 0 and cli_report.get("status") == "PASS",
        {"returncode": completed.returncode, "report": cli_report},
    )

    for owner in ("main", "planner"):
        report = _project_report(owner=owner)
        _record(
            checks,
            f"valid-{owner}-initial-cycle-with-seed-cycle-omitted",
            report["status"] == "PASS",
            report,
        )

    report = _project_report(write_session=False)
    _record(
        checks,
        "missing-current-session-state-rejected",
        _fails(report, f"missing {checker.SESSION_RELATIVE}"),
        report,
    )

    def stale_current_session(session: dict[str, Any]) -> None:
        session["session_id"] = "sess-new"

    report = _project_report(session_mutator=stale_current_session)
    _record(
        checks,
        "stale-cross-session-evidence-rejected",
        _fails(report, "must belong to the current OMX session"),
        report,
    )

    def explicit_initial_mode_cycle(mode_state: dict[str, Any]) -> None:
        mode_state["review_cycle"] = INITIAL_REVIEW_CYCLE + 1

    report = _project_report(mode_state_mutator=explicit_initial_mode_cycle)
    _record(
        checks,
        "stale-current-review-cycle-rejected",
        _fails(report, "current OMX review_cycle"),
        report,
    )

    report = _project_report(write_mode_state=False)
    _record(
        checks,
        "missing-current-mode-state-rejected",
        _fails(report, "missing current OMX mode state"),
        report,
    )

    report = _project_report(review_cycle=1)
    _record(
        checks,
        "omitted-initial-mode-cycle-binds-only-cycle-zero",
        _fails(report, "binds only to review_cycle 0"),
        report,
    )

    report = _project_report(
        mode_state_mutator=return_mode_state,
        review_cycle=RETURN_REVIEW_CYCLE,
    )
    _record(
        checks,
        "fresh-return-to-ralplan-cycle-accepted",
        report["status"] == "PASS",
        report,
    )

    report = _project_report(
        mode_state_mutator=return_mode_state,
        review_cycle=RETURN_PARENT_CYCLE,
    )
    _record(
        checks,
        "stale-return-to-ralplan-cycle-rejected",
        _fails(report, "greater than parent review_cycle"),
        report,
    )

    def return_without_parent_cycle(mode_state: dict[str, Any]) -> None:
        mode_state.update(
            {
                "current_phase": "ralplan",
                "return_to_ralplan_reason": "QA findings require replanning",
            }
        )

    report = _project_report(
        mode_state_mutator=return_without_parent_cycle,
        review_cycle=RETURN_REVIEW_CYCLE,
    )
    _record(
        checks,
        "return-to-ralplan-without-parent-cycle-rejected",
        _fails(report, "does not provide a parent review_cycle"),
        report,
    )

    def persisted_advanced_return_cycle(mode_state: dict[str, Any]) -> None:
        mode_state.update(
            {
                "current_phase": "ralplan",
                "review_cycle": RETURN_REVIEW_CYCLE + 1,
                "return_to_ralplan_parent_review_cycle": RETURN_PARENT_CYCLE,
                "return_to_ralplan_reason": "QA findings require replanning",
            }
        )

    report = _project_report(
        mode_state_mutator=persisted_advanced_return_cycle,
        review_cycle=RETURN_REVIEW_CYCLE,
    )
    _record(
        checks,
        "persisted-advanced-return-cycle-must-match-current-state",
        _fails(report, "current advanced OMX review_cycle"),
        report,
    )

    def stale_architect_cycle(payload: dict[str, Any]) -> None:
        architect, _ = _reviews(payload)
        architect["review_cycle"] = RETURN_PARENT_CYCLE

    report = _project_report(
        stale_architect_cycle,
        mode_state_mutator=return_mode_state,
        review_cycle=RETURN_REVIEW_CYCLE,
    )
    _record(
        checks,
        "architect-return-review-cycle-freshness-required",
        _fails(report, "architect review_cycle"),
        report,
    )

    def stale_critic_cycle(payload: dict[str, Any]) -> None:
        _, critic = _reviews(payload)
        critic["review_cycle"] = RETURN_PARENT_CYCLE

    report = _project_report(
        stale_critic_cycle,
        mode_state_mutator=return_mode_state,
        review_cycle=RETURN_REVIEW_CYCLE,
    )
    _record(
        checks,
        "critic-return-review-cycle-freshness-required",
        _fails(report, "critic review_cycle"),
        report,
    )

    def wrong_prd_hash(payload: dict[str, Any]) -> None:
        payload["planning_artifacts"]["prd_sha256"] = "0" * 64

    report = _project_report(wrong_prd_hash)
    _record(
        checks,
        "recorded-prd-hash-mismatch-rejected",
        _fails(report, "prd_sha256 does not match"),
        report,
    )

    report = _project_report(artifact_bytes=b"# revised after approval\n")
    _record(
        checks,
        "post-approval-artifact-byte-change-rejected",
        _fails(report, "does not match the current"),
        report,
    )

    def naive_review_timestamp(payload: dict[str, Any]) -> None:
        architect, _ = _reviews(payload)
        architect["completed_at"] = "2026-07-23T10:00:00"

    report = _project_report(naive_review_timestamp)
    _record(
        checks,
        "naive-review-timestamp-rejected",
        _fails(report, "completed_at"),
        report,
    )

    def naive_tracker_timestamp(tracker: dict[str, Any]) -> None:
        tracker["sessions"]["sess-demo"]["threads"]["thread-architect"]["completed_at"] = (
            "2026-07-23T10:00:00"
        )

    report = _project_report(tracker_mutator=naive_tracker_timestamp)
    _record(
        checks,
        "naive-tracker-timestamp-rejected",
        _fails(report, "timezone-bearing RFC 3339"),
        report,
    )

    def omit_optional_tracker_leader(tracker: dict[str, Any]) -> None:
        del tracker["sessions"]["sess-demo"]["leader_thread_id"]

    report = _project_report(tracker_mutator=omit_optional_tracker_leader)
    _record(
        checks,
        "tracker-leader-thread-id-is-optional",
        report["status"] == "PASS",
        report,
    )

    differential = _omx_0203_differential()
    _record(
        checks,
        "installed-omx-0.20.3-initial-return-and-shape-differential",
        differential["status"] in {"PASS", "SKIP"},
        differential,
    )

    def pending(payload: dict[str, Any]) -> None:
        payload["evidence_status"] = "pending"
        payload["ralplan_consensus_gate"]["complete"] = False
        payload["ralplan_consensus_gate"]["blocked_reason"] = "evidence_not_yet_recorded"

    report = _project_report(pending)
    _record(
        checks,
        "pending-project-fails-closed",
        _fails(report, "evidence_status must be complete"),
        report,
    )

    def unavailable(payload: dict[str, Any]) -> None:
        payload["evidence_status"] = "blocked"
        payload["role_routing"] = {
            "status": "unavailable",
            "surface": "role_routing_unavailable",
            "documented_leader_proof": False,
            "blocked_reason": "unsupported_documented_leader_proof",
        }
        payload["ralplan_consensus_gate"]["complete"] = False
        payload["ralplan_consensus_gate"]["blocked_reason"] = "unsupported_documented_leader_proof"

    report = _project_report(unavailable)
    _record(
        checks,
        "unavailable-role-routing-fails-closed",
        _fails(report, "unsupported_documented_leader_proof"),
        report,
    )

    def no_leader_proof(payload: dict[str, Any]) -> None:
        payload["evidence_status"] = "blocked"
        payload["role_routing"] = {
            "status": "pending",
            "surface": "pending",
            "documented_leader_proof": False,
            "blocked_reason": "documented_leader_proof_unavailable",
        }
        payload["ralplan_consensus_gate"]["complete"] = False
        payload["ralplan_consensus_gate"]["blocked_reason"] = "documented_leader_proof_unavailable"

    report = _project_report(no_leader_proof)
    _record(
        checks,
        "missing-documented-leader-proof-fails",
        _fails(report, "documented native leader proof"),
        report,
    )

    def adapted(payload: dict[str, Any]) -> None:
        architect, _ = _reviews(payload)
        architect["provenance_kind"] = "omx_adapted"

    report = _project_report(adapted)
    _record(
        checks,
        "adapted-provenance-rejected",
        _fails(report, "native_subagent"),
        report,
    )

    def iterate(payload: dict[str, Any]) -> None:
        architect, _ = _reviews(payload)
        architect["verdict"] = "iterate"

    report = _project_report(iterate)
    _record(
        checks,
        "non-approving-verdict-rejected",
        _fails(report, "approve"),
        report,
    )

    report = _project_report(write_tracker=False)
    _record(
        checks,
        "missing-tracker-rejected",
        _fails(report, "missing .omx/state/subagent-tracking.json"),
        report,
    )

    def reused_thread(payload: dict[str, Any]) -> None:
        _, critic = _reviews(payload)
        critic["thread_id"] = "thread-architect"

    report = _project_report(reused_thread)
    _record(
        checks,
        "reused-review-thread-rejected",
        _fails(report, "distinct thread_id"),
        report,
    )

    def incomplete_architect(tracker: dict[str, Any]) -> None:
        del tracker["sessions"]["sess-demo"]["threads"]["thread-architect"]["completed_at"]

    report = _project_report(tracker_mutator=incomplete_architect)
    _record(
        checks,
        "incomplete-architect-thread-rejected",
        _fails(report, "architect.completed_at"),
        report,
    )

    def reversed_order(tracker: dict[str, Any]) -> None:
        tracker["sessions"]["sess-demo"]["threads"]["thread-architect"]["completed_at"] = (
            "2026-07-23T10:02:00.000Z"
        )

    report = _project_report(tracker_mutator=reversed_order)
    _record(
        checks,
        "reversed-review-order-rejected",
        _fails(report, "strictly before"),
        report,
    )

    def wrong_role(tracker: dict[str, Any]) -> None:
        tracker["sessions"]["sess-demo"]["threads"]["thread-architect"]["role"] = "planner"

    report = _project_report(tracker_mutator=wrong_role)
    _record(
        checks,
        "tracker-role-mismatch-rejected",
        _fails(report, "expected 'architect'"),
        report,
    )

    def leader_review(payload: dict[str, Any]) -> None:
        architect, _ = _reviews(payload)
        architect["thread_id"] = "thread-leader"

    report = _project_report(leader_review)
    _record(
        checks,
        "leader-self-review-rejected",
        _fails(report, "session leader"),
        report,
    )

    def session_only_leader(payload: dict[str, Any]) -> None:
        architect, _ = _reviews(payload)
        architect["thread_id"] = "thread-leader"

    def hide_tracker_leader_identity(tracker: dict[str, Any]) -> None:
        session = tracker["sessions"]["sess-demo"]
        del session["leader_thread_id"]
        leader = session["threads"]["thread-leader"]
        leader.update(
            {
                "kind": "subagent",
                "role": "architect",
                "provenance_kind": "native_subagent",
                "completed_at": "2026-07-23T10:00:00.000Z",
            }
        )

    report = _project_report(
        session_only_leader,
        hide_tracker_leader_identity,
    )
    _record(
        checks,
        "session-state-native-leader-self-review-rejected",
        _fails(report, "current session leader"),
        report,
    )

    def different_sessions(payload: dict[str, Any]) -> None:
        _, critic = _reviews(payload)
        critic["session_id"] = "sess-other"

    report = _project_report(different_sessions)
    _record(
        checks,
        "cross-session-reviews-rejected",
        _fails(report, "same session_id"),
        report,
    )

    report = _project_report(write_artifacts=False)
    _record(
        checks,
        "missing-planning-artifacts-rejected",
        _fails(report, "does not exist"),
        report,
    )

    def started_at_fallback(tracker: dict[str, Any]) -> None:
        critic = tracker["sessions"]["sess-demo"]["threads"]["thread-critic"]
        critic["started_at"] = critic.pop("first_seen_at")

    report = _project_report(tracker_mutator=started_at_fallback)
    _record(
        checks,
        "critic-started-at-fallback",
        report["status"] == "PASS",
        report,
    )

    def roleless_legacy_native(tracker: dict[str, Any]) -> None:
        threads = tracker["sessions"]["sess-demo"]["threads"]
        del threads["thread-architect"]["role"]
        del threads["thread-critic"]["role"]

    report = _project_report(tracker_mutator=roleless_legacy_native)
    _record(
        checks,
        "roleless-legacy-native-tracker-compatible",
        report["status"] == "PASS",
        report,
    )

    def conflicting_provenance(tracker: dict[str, Any]) -> None:
        tracker["sessions"]["sess-demo"]["threads"]["thread-critic"]["provenance_kind"] = (
            "omx_adapted"
        )

    report = _project_report(tracker_mutator=conflicting_provenance)
    _record(
        checks,
        "conflicting-tracker-provenance-rejected",
        _fails(report, "conflicts with native_subagent"),
        report,
    )

    def wrong_kind(tracker: dict[str, Any]) -> None:
        tracker["sessions"]["sess-demo"]["threads"]["thread-critic"]["kind"] = "leader"

    report = _project_report(tracker_mutator=wrong_kind)
    _record(
        checks,
        "non-subagent-review-thread-rejected",
        _fails(report, "kind must be subagent"),
        report,
    )

    def incomplete_critic(tracker: dict[str, Any]) -> None:
        del tracker["sessions"]["sess-demo"]["threads"]["thread-critic"]["completed_at"]

    report = _project_report(tracker_mutator=incomplete_critic)
    _record(
        checks,
        "incomplete-critic-thread-rejected",
        _fails(report, "critic.completed_at"),
        report,
    )

    def wrong_sequence(payload: dict[str, Any]) -> None:
        payload["ralplan_consensus_gate"]["sequence"] = [
            "critic-review",
            "architect-review",
        ]

    report = _project_report(wrong_sequence)
    _record(
        checks,
        "wrong-consensus-sequence-rejected",
        _fails(report, "architect-review"),
        report,
    )

    with tempfile.TemporaryDirectory(prefix="z2h-planning-template-") as temp:
        root = Path(temp)
        missing_field_payload = _payload()
        del missing_field_payload["planning_artifacts"]
        _write_evidence(root / checker.TEMPLATE_RELATIVE, missing_field_payload)
        report = checker.check_planning_evidence(
            root,
            mode="template",
            schema_path=SCHEMA,
        )
    _record(
        checks,
        "template-required-field-enforced",
        _fails(report, "planning_artifacts"),
        report,
    )

    with tempfile.TemporaryDirectory(prefix="z2h-planning-markers-") as temp:
        root = Path(temp)
        path = root / checker.TEMPLATE_RELATIVE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Planning evidence\n", encoding="utf-8")
        report = checker.check_planning_evidence(
            root,
            mode="template",
            schema_path=SCHEMA,
        )
    _record(
        checks,
        "marker-contract-enforced",
        _fails(report, "marker pair"),
        report,
    )

    with tempfile.TemporaryDirectory(prefix="z2h-planning-marker-order-") as temp:
        root = Path(temp)
        path = root / checker.TEMPLATE_RELATIVE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"{checker.END_MARKER}\n{checker.START_MARKER}\n",
            encoding="utf-8",
        )
        report = checker.check_planning_evidence(
            root,
            mode="template",
            schema_path=SCHEMA,
        )
    _record(
        checks,
        "marker-order-enforced",
        _fails(report, "marker order"),
        report,
    )

    failures = [item for item in checks if not item["ok"]]
    return {
        "status": "PASS" if not failures else "FAIL",
        "checks": len(checks),
        "failures": failures,
        "results": checks,
    }


def main() -> int:
    report = run_tests()
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif report["status"] == "PASS":
        print(f"planning-evidence contract tests: PASS ({report['checks']} checks)")
    else:
        print("planning-evidence contract tests: FAIL")
        for failure in report["failures"]:
            print(f"ERROR: {failure['check']}: {failure['detail']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
