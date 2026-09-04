#!/usr/bin/env python3
"""Bounded external integration test for the audited OMX Ultragoal interface."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import omx_adapter  # noqa: E402


class IntegrationFailure(RuntimeError):
    pass


def _assert(checks: list[dict[str, Any]], condition: bool, name: str, detail: Any = None) -> None:
    checks.append({"check": name, "ok": bool(condition), "detail": detail})
    if not condition:
        raise IntegrationFailure(f"{name}: {detail}")


def _run_json(
    *,
    probe: Mapping[str, Any],
    cwd: Path,
    args: list[str],
    timeout: int,
    env_overrides: Mapping[str, str | None],
) -> tuple[dict[str, Any], dict[str, Any]]:
    run = omx_adapter.run_bounded(
        [str(probe["cli_path"]), "ultragoal", *args, "--json"],
        cwd=cwd,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    if run["timed_out"]:
        raise IntegrationFailure(f"{' '.join(args)} timed out after {timeout} seconds")
    if run["returncode"] != 0:
        raise IntegrationFailure(
            f"{' '.join(args)} failed with {run['returncode']}: {run['stderr'] or run['stdout']}"
        )
    try:
        return json.loads(run["stdout"]), run
    except json.JSONDecodeError as exc:
        raise IntegrationFailure(f"{' '.join(args)} emitted invalid JSON: {exc}") from exc


def _run_rejected_json(
    *,
    probe: Mapping[str, Any],
    cwd: Path,
    args: list[str],
    timeout: int,
    env_overrides: Mapping[str, str | None],
) -> tuple[dict[str, Any], dict[str, Any]]:
    run = omx_adapter.run_bounded(
        [str(probe["cli_path"]), "ultragoal", *args, "--json"],
        cwd=cwd,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    if run["timed_out"]:
        raise IntegrationFailure(f"{' '.join(args)} timed out after {timeout} seconds")
    if run["returncode"] == 0:
        raise IntegrationFailure(f"{' '.join(args)} unexpectedly succeeded")
    try:
        return json.loads(run["stdout"]), run
    except json.JSONDecodeError as exc:
        raise IntegrationFailure(
            f"{' '.join(args)} emitted invalid rejection JSON: {exc}"
        ) from exc


def _read_ledger(root: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (root / ".omx/ultragoal/ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]


def _goal(plan: Mapping[str, Any], goal_id: str) -> dict[str, Any]:
    for candidate in plan.get("goals", []):
        if isinstance(candidate, dict) and candidate.get("id") == goal_id:
            return candidate
    raise IntegrationFailure(f"plan does not contain goal {goal_id}")


def _clean_quality_gate() -> dict[str, Any]:
    return {
        "aiSlopCleaner": {
            "status": "passed",
            "evidence": "synthetic anti-slop cleanup passed",
        },
        "verification": {
            "status": "passed",
            "commands": ["synthetic verification"],
            "evidence": "synthetic verification passed after cleanup",
        },
        "codeReview": {
            "recommendation": "APPROVE",
            "architectStatus": "CLEAR",
            "evidence": "synthetic independent review approved the probe",
            "independentReview": {
                "codeReviewer": {
                    "agentRole": "code-reviewer",
                    "evidence": "synthetic code-reviewer returned APPROVE",
                },
                "architect": {
                    "agentRole": "architect",
                    "evidence": "synthetic architect returned CLEAR",
                },
            },
        },
        "architectureInvariantGate": {
            "status": "passed",
            "sourceArtifacts": [
                ".omx/ultragoal/brief.md",
                ".omx/ultragoal/goals.json",
            ],
            "invariants": [],
            "evidence": "the synthetic brief declared no architecture invariants",
        },
    }


def run_timeout_regression() -> list[dict[str, Any]]:
    """Prove a timeout cannot be mistaken for success or leave a POSIX child alive."""

    checks: list[dict[str, Any]] = []
    supports_tree_assertion = os.name == "posix" and hasattr(os, "killpg")
    with tempfile.TemporaryDirectory(prefix="zero-to-hero-omx-timeout-") as temp:
        root = Path(temp)
        ready = root / "child-ready"
        delayed_write = root / "descendant-write"

        if supports_tree_assertion:
            child_code = (
                "import os, pathlib, signal, sys, time\n"
                "ready = pathlib.Path(sys.argv[1])\n"
                "output = pathlib.Path(sys.argv[2])\n"
                "parent_pid = int(sys.argv[3])\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "ready.write_text(str(os.getpid()), encoding='utf-8')\n"
                "while os.getppid() == parent_pid:\n"
                "    time.sleep(0.02)\n"
                "time.sleep(0.25)\n"
                "output.write_text('descendant survived timeout', encoding='utf-8')\n"
            )
            parent_code = (
                "import os, pathlib, subprocess, sys, time\n"
                "ready = pathlib.Path(sys.argv[1])\n"
                "subprocess.Popen([sys.executable, '-c', sys.argv[3], "
                "str(ready), sys.argv[2], str(os.getpid())])\n"
                "deadline = time.monotonic() + 5\n"
                "while not ready.exists() and time.monotonic() < deadline:\n"
                "    time.sleep(0.02)\n"
                "time.sleep(30)\n"
            )
            command = [
                sys.executable,
                "-c",
                parent_code,
                str(ready),
                str(delayed_write),
                child_code,
            ]
            timeout = 1.0
        else:
            command = [sys.executable, "-c", "import time; time.sleep(30)"]
            timeout = 0.5

        started = time.monotonic()
        run = omx_adapter.run_bounded(command, cwd=root, timeout=timeout)
        elapsed = time.monotonic() - started

        _assert(checks, run["timed_out"] is True, "timeout:reported", run)
        _assert(
            checks,
            run["returncode"] is None,
            "timeout:not-success",
            run.get("returncode"),
        )
        termination = run.get("termination", {})
        _assert(
            checks,
            termination.get("direct_process_exited") is True,
            "timeout:direct-process-exited",
            termination,
        )
        expected_isolation = {
            "posix": "posix_session",
            "nt": "windows_process_group",
        }.get(os.name)
        if expected_isolation is not None:
            _assert(
                checks,
                run.get("process_isolation") == expected_isolation,
                "timeout:isolated-process-group",
                run.get("process_isolation"),
            )
        _assert(
            checks,
            elapsed < 8,
            "timeout:bounded-cleanup",
            {"elapsed_seconds": round(elapsed, 3), "timeout_seconds": timeout},
        )

        if supports_tree_assertion:
            _assert(
                checks,
                ready.is_file(),
                "timeout:descendant-started",
                str(ready),
            )
            time.sleep(0.75)
            _assert(
                checks,
                not delayed_write.exists(),
                "timeout:no-descendant-write",
                str(delayed_write),
            )
        else:
            checks.append(
                {
                    "check": "timeout:no-descendant-write",
                    "ok": True,
                    "status": "SKIP",
                    "detail": (
                        "A guaranteed stdlib descendant-kill primitive is unavailable on "
                        "this platform; process-group isolation plus the direct-process "
                        "timeout and termination assertions still ran."
                    ),
                }
            )
    return checks


def run_structured_steering_integration(
    *,
    probe: Mapping[str, Any],
    parent: Path,
    timeout: int,
    env_overrides: Mapping[str, str | None],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    root = parent / "structured-steering"
    root.mkdir()

    created, _ = _run_json(
        probe=probe,
        cwd=root,
        args=[
            "create-goals",
            "--brief",
            "Exercise the audited structured steering contract without changing its constraints.",
            "--goal",
            "Alpha::Complete alpha with deterministic evidence.",
            "--goal",
            "Beta::Complete beta with deterministic evidence.",
            "--goal",
            "Gamma::Complete gamma with deterministic evidence.",
            "--goal",
            "Delta::Complete delta with deterministic evidence.",
        ],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    initial_plan = created["plan"]
    initial_goal_ids = [goal["id"] for goal in initial_plan["goals"]]
    aggregate_objective = initial_plan["codexObjective"]
    initial_brief = (root / ".omx/ultragoal/brief.md").read_text(encoding="utf-8")
    _assert(
        checks,
        len(initial_goal_ids) == 4,
        "steering:create-explicit-goals",
        initial_goal_ids,
    )

    add_args = [
        "steer",
        "--kind",
        "add_subgoal",
        "--title",
        "Epsilon",
        "--objective",
        "Complete epsilon with deterministic evidence.",
        "--evidence",
        "The compatibility probe needs an appended schedule-eligible goal.",
        "--rationale",
        "Appending a bounded goal preserves the aggregate objective and original constraints.",
        "--idempotency-key",
        "integration-add-epsilon",
    ]
    added, _ = _run_json(
        probe=probe,
        cwd=root,
        args=add_args,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    added_ids = [
        goal["id"] for goal in added["plan"]["goals"] if goal["id"] not in initial_goal_ids
    ]
    _assert(checks, added["accepted"] is True, "steering:add:accepted", added["audit"])
    _assert(
        checks,
        added["audit"]["targetGoalIds"] == [],
        "steering:add:no-target",
        added["audit"],
    )
    _assert(
        checks,
        len(added_ids) == 1 and _goal(added["plan"], added_ids[0])["status"] == "pending",
        "steering:add:pending-goal-appended",
        added_ids,
    )
    added_goal_id = added_ids[0]
    ledger_after_add = _read_ledger(root)

    replayed, _ = _run_json(
        probe=probe,
        cwd=root,
        args=add_args,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    ledger_after_replay = _read_ledger(root)
    _assert(
        checks,
        replayed["accepted"] is True and replayed["deduped"] is True,
        "steering:add:idempotent-replay-deduped",
        replayed["audit"],
    )
    _assert(
        checks,
        len(ledger_after_replay) == len(ledger_after_add),
        "steering:add:dedupe-reuses-ledger-audit",
        {
            "before": len(ledger_after_add),
            "after": len(ledger_after_replay),
        },
    )

    split_target = initial_goal_ids[0]
    split, _ = _run_json(
        probe=probe,
        cwd=root,
        args=[
            "steer",
            "--kind",
            "split_subgoal",
            "--target-goal-id",
            split_target,
            "--evidence",
            "Alpha contains two independently verifiable slices.",
            "--rationale",
            "Replacement children isolate verification without deleting the original goal.",
            "--after-json",
            json.dumps(
                {
                    "children": [
                        {
                            "title": "Alpha one",
                            "objective": "Complete alpha one with deterministic evidence.",
                        },
                        {
                            "title": "Alpha two",
                            "objective": "Complete alpha two with deterministic evidence.",
                        },
                    ]
                }
            ),
            "--idempotency-key",
            "integration-split-alpha",
        ],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    split_parent = _goal(split["plan"], split_target)
    split_children = split_parent.get("supersededBy", [])
    _assert(
        checks,
        split["accepted"] is True
        and split_parent.get("steeringStatus") == "superseded",
        "steering:split:parent-retained-superseded",
        split_parent,
    )
    _assert(
        checks,
        len(split_children) == 2
        and all(_goal(split["plan"], child)["status"] == "pending" for child in split_children),
        "steering:split:replacement-children",
        split_children,
    )

    revise_target = initial_goal_ids[1]
    directive_path = root / "revise-directive.json"
    directive_path.write_text(
        json.dumps(
            {
                "kind": "revise_pending_wording",
                "source": "finding",
                "targetGoalId": revise_target,
                "title": "Beta clarified",
                "objective": "Complete clarified beta with deterministic evidence.",
                "evidence": "The Beta wording was ambiguous during the compatibility probe.",
                "rationale": "Clarifying wording preserves status, constraints, and verification.",
                "idempotencyKey": "integration-revise-beta",
            }
        ),
        encoding="utf-8",
    )
    revised, _ = _run_json(
        probe=probe,
        cwd=root,
        args=["steer", "--directive-json", str(directive_path)],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    revised_goal = _goal(revised["plan"], revise_target)
    _assert(
        checks,
        revised["accepted"] is True and revised["audit"]["source"] == "finding",
        "steering:revise:directive-json-accepted",
        revised["audit"],
    )
    _assert(
        checks,
        revised_goal["title"] == "Beta clarified"
        and revised_goal["objective"]
        == "Complete clarified beta with deterministic evidence."
        and revised_goal["status"] == "pending",
        "steering:revise:wording-only",
        revised_goal,
    )

    schedule_eligible = [
        goal["id"]
        for goal in revised["plan"]["goals"]
        if goal["status"] == "pending"
        and goal.get("steeringStatus") not in {"superseded", "blocked"}
    ]
    requested_order = list(reversed(schedule_eligible))
    reordered, _ = _run_json(
        probe=probe,
        cwd=root,
        args=[
            "steer",
            "--kind",
            "reorder_pending",
            "--evidence",
            "The reverse synthetic order makes the mutation observable.",
            "--rationale",
            "Only schedule-eligible pending goals are included in the requested order.",
            "--after-json",
            json.dumps({"pendingGoalIds": requested_order}),
            "--idempotency-key",
            "integration-reorder-pending",
        ],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    _assert(
        checks,
        reordered["accepted"] is True,
        "steering:reorder:accepted",
        reordered["audit"],
    )
    _assert(
        checks,
        [goal["id"] for goal in reordered["plan"]["goals"][: len(requested_order)]]
        == requested_order,
        "steering:reorder:after-pending-goal-ids",
        [goal["id"] for goal in reordered["plan"]["goals"]],
    )

    annotate_target = initial_goal_ids[2]
    plan_before_annotation = json.dumps(reordered["plan"], sort_keys=True)
    annotated, _ = _run_json(
        probe=probe,
        cwd=root,
        args=[
            "steer",
            "--kind",
            "annotate_ledger",
            "--source",
            "user_prompt_submit",
            "--target-goal-id",
            annotate_target,
            "--evidence",
            "A structured prompt-submit directive was explicitly supplied.",
            "--rationale",
            "The evidence belongs in the ledger without changing scheduling.",
            "--idempotency-key",
            "integration-annotate-gamma",
        ],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    _assert(
        checks,
        annotated["accepted"] is True
        and annotated["audit"]["source"] == "user_prompt_submit",
        "steering:annotate:accepted-source",
        annotated["audit"],
    )
    _assert(
        checks,
        json.dumps(annotated["plan"], sort_keys=True) == plan_before_annotation,
        "steering:annotate:no-plan-mutation",
        annotated["audit"],
    )

    blocked_target = initial_goal_ids[3]
    blocked_rationale = (
        "The current Delta path is evidence-backed as blocked and has no safe replacement yet."
    )
    marked_blocked, _ = _run_json(
        probe=probe,
        cwd=root,
        args=[
            "steer",
            "--kind",
            "mark_blocked_superseded",
            "--target-goal-id",
            blocked_target,
            "--evidence",
            "The synthetic Delta dependency is unavailable.",
            "--rationale",
            blocked_rationale,
            "--idempotency-key",
            "integration-block-delta",
        ],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    blocked_goal = _goal(marked_blocked["plan"], blocked_target)
    _assert(
        checks,
        blocked_goal.get("steeringStatus") == "blocked"
        and blocked_goal.get("blockedReason") == blocked_rationale,
        "steering:mark-blocked:without-replacement",
        blocked_goal,
    )

    superseded, _ = _run_json(
        probe=probe,
        cwd=root,
        args=[
            "steer",
            "--kind",
            "mark_blocked_superseded",
            "--target-goal-id",
            revise_target,
            "--evidence",
            "A safer replacement path for clarified Beta is now available.",
            "--rationale",
            "The replacement keeps the original goal audit-visible and restores a safe path.",
            "--after-json",
            json.dumps(
                {
                    "children": [
                        {
                            "title": "Beta replacement",
                            "objective": "Complete the safer Beta replacement with evidence.",
                        }
                    ]
                }
            ),
            "--idempotency-key",
            "integration-supersede-beta",
        ],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    superseded_goal = _goal(superseded["plan"], revise_target)
    replacement_ids = superseded_goal.get("supersededBy", [])
    _assert(
        checks,
        superseded_goal.get("steeringStatus") == "superseded"
        and len(replacement_ids) == 1
        and _goal(superseded["plan"], replacement_ids[0])["status"] == "pending",
        "steering:mark-blocked:superseded-with-replacement",
        superseded_goal,
    )

    plan_before_rejection = json.dumps(superseded["plan"], sort_keys=True)
    rejected, rejected_run = _run_rejected_json(
        probe=probe,
        cwd=root,
        args=[
            "steer",
            "--kind",
            "revise_pending_wording",
            "--target-goal-id",
            added_goal_id,
            "--evidence",
            "The rejection probe intentionally proposes protected state.",
            "--rationale",
            "This would bypass verification and weaken the quality gate.",
            "--after-json",
            json.dumps(
                {
                    "title": "Unsafe rewrite",
                    "codexObjective": "Complete a smaller objective.",
                    "qualityGate": {"verification": {"status": "skipped"}},
                }
            ),
            "--idempotency-key",
            "integration-reject-protected",
        ],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    _assert(
        checks,
        rejected_run["returncode"] == 1 and rejected["accepted"] is False,
        "steering:protected-mutation-rejected",
        rejected,
    )
    _assert(
        checks,
        any("protected objective" in reason for reason in rejected["rejectedReasons"])
        and any("must not weaken" in reason for reason in rejected["rejectedReasons"]),
        "steering:protected-rejection-reasons",
        rejected["rejectedReasons"],
    )
    _assert(
        checks,
        json.dumps(rejected["plan"], sort_keys=True) == plan_before_rejection,
        "steering:rejected-plan-unchanged",
        rejected["audit"],
    )

    ledger_before_broad_prose = _read_ledger(root)
    plan_before_broad_prose = (root / ".omx/ultragoal/goals.json").read_text(
        encoding="utf-8"
    )
    broad_prose = omx_adapter.run_bounded(
        [
            str(probe["cli_path"]),
            "ultragoal",
            "steer",
            "please rewrite the goals however seems best",
        ],
        cwd=root,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    broad_output = f"{broad_prose['stdout']}\n{broad_prose['stderr']}"
    _assert(
        checks,
        broad_prose["returncode"] != 0
        and "rejects broad natural-language mutation requests" in broad_output,
        "steering:broad-prose-rejected",
        broad_output,
    )
    _assert(
        checks,
        len(_read_ledger(root)) == len(ledger_before_broad_prose)
        and (root / ".omx/ultragoal/goals.json").read_text(encoding="utf-8")
        == plan_before_broad_prose,
        "steering:broad-prose-no-mutation",
        None,
    )

    plural_target = omx_adapter.run_bounded(
        [
            str(probe["cli_path"]),
            "ultragoal",
            "steer",
            "--kind",
            "annotate_ledger",
            "--target-goal-ids",
            f"{annotate_target},{added_goal_id}",
            "--evidence",
            "Probe the plural target synopsis.",
            "--rationale",
            "The adapter must not rely on an advertised-only flag.",
            "--json",
        ],
        cwd=root,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    plural_output = f"{plural_target['stdout']}\n{plural_target['stderr']}"
    _assert(
        checks,
        plural_target["returncode"] != 0
        and "rejects broad natural-language mutation requests" in plural_output,
        "steering:plural-target-flag-advertised-only",
        plural_output,
    )
    _assert(
        checks,
        len(_read_ledger(root)) == len(ledger_before_broad_prose),
        "steering:plural-target-rejection-no-ledger-mutation",
        len(_read_ledger(root)),
    )

    final_plan = json.loads(
        (root / ".omx/ultragoal/goals.json").read_text(encoding="utf-8")
    )
    final_ledger = _read_ledger(root)
    accepted_entries = [
        entry for entry in final_ledger if entry.get("event") == "steering_accepted"
    ]
    rejected_entries = [
        entry for entry in final_ledger if entry.get("event") == "steering_rejected"
    ]
    _assert(
        checks,
        {entry.get("mutationKind") for entry in accepted_entries}
        == set(omx_adapter.STEERING_MUTATION_KINDS),
        "steering:all-six-mutation-kinds-audited",
        [entry.get("mutationKind") for entry in accepted_entries],
    )
    _assert(
        checks,
        len(rejected_entries) == 1
        and rejected_entries[0].get("steering", {})
        .get("invariant", {})
        .get("accepted")
        is False,
        "steering:accepted-and-rejected-ledger-audits",
        {
            "accepted": len(accepted_entries),
            "rejected": len(rejected_entries),
        },
    )
    _assert(
        checks,
        final_plan["codexObjective"] == aggregate_objective
        and final_plan.get("aggregateCompletion") is None
        and (root / ".omx/ultragoal/brief.md").read_text(encoding="utf-8")
        == initial_brief,
        "steering:protected-aggregate-state-immutable",
        {
            "codexObjective": final_plan.get("codexObjective"),
            "aggregateCompletion": final_plan.get("aggregateCompletion"),
        },
    )
    _assert(
        checks,
        set(initial_goal_ids).issubset(
            {goal["id"] for goal in final_plan["goals"]}
        )
        and all(goal["status"] != "complete" for goal in final_plan["goals"]),
        "steering:no-hard-delete-or-auto-complete",
        [goal["id"] for goal in final_plan["goals"]],
    )

    cleanup_root = parent / "same-thread-cleanup"
    cleanup_root.mkdir()
    cleanup_task_objective = "Finish one synthetic item with verification."
    cleanup_created, _ = _run_json(
        probe=probe,
        cwd=cleanup_root,
        args=[
            "create-goals",
            "--brief",
            cleanup_task_objective,
            "--goal",
            "Single::Complete the single synthetic item with verification.",
        ],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    cleanup_goal_id = cleanup_created["plan"]["goals"][0]["id"]
    _run_json(
        probe=probe,
        cwd=cleanup_root,
        args=["complete-goals"],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    cleanup_run = omx_adapter.run_bounded(
        [
            str(probe["cli_path"]),
            "ultragoal",
            "checkpoint",
            "--goal-id",
            cleanup_goal_id,
            "--status",
            "complete",
            "--evidence",
            (
                "Completed implementation for "
                f".omx/ultragoal/goals.json {cleanup_goal_id}; synthetic validation "
                "and independent review passed."
            ),
            "--codex-goal-json",
            json.dumps(
                {
                    "goal": {
                        "objective": cleanup_task_objective,
                        "status": "complete",
                    }
                }
            ),
            "--quality-gate-json",
            json.dumps(_clean_quality_gate()),
        ],
        cwd=cleanup_root,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    cleanup_output = f"{cleanup_run['stdout']}\n{cleanup_run['stderr']}"
    _assert(
        checks,
        cleanup_run["returncode"] == 0
        and (
            "run /goal clear in the Codex UI before calling create_goal for the next "
            "OMX goal"
        )
        in cleanup_output,
        "goal-clear:terminal-notice-after-completed-aggregate",
        cleanup_output,
    )
    _assert(
        checks,
        "do not call /goal clear or hidden thread/goal/clear routes" in cleanup_output,
        "goal-clear:omx-does-not-invoke-hidden-clear",
        cleanup_output,
    )
    cleanup_status, _ = _run_json(
        probe=probe,
        cwd=cleanup_root,
        args=["status"],
        timeout=timeout,
        env_overrides=env_overrides,
    )
    _assert(
        checks,
        cleanup_status["summary"]["aggregateComplete"] is True,
        "goal-clear:notice-follows-terminal-completion",
        cleanup_status["summary"],
    )

    return checks


def run_integration(probe: Mapping[str, Any], timeout: int) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    leader_env = {
        "OMX_TEAM_WORKER": None,
        "OMX_TEAM_INTERNAL_WORKER": None,
    }

    with tempfile.TemporaryDirectory(prefix="zero-to-hero-omx-") as temp:
        root = Path(temp)
        brief = root / "implementation-brief.md"
        brief.write_text(
            "# Synthetic implementation brief\n\n"
            "- Complete the first synthetic milestone with deterministic evidence.\n"
            "- Exercise the second synthetic milestone blocker path.\n",
            encoding="utf-8",
        )

        create = omx_adapter.execute_create_goals(
            repo=root,
            brief_file=brief,
            probe=probe,
            timeout=timeout,
            env_overrides=leader_env,
        )
        _assert(checks, create["status"] == "PASS", "create-goals", create.get("message"))
        for relative in omx_adapter.RUNTIME_ARTIFACTS:
            _assert(
                checks,
                (root / relative).is_file(),
                f"runtime-artifact:{relative}",
                "created by compatible OMX CLI",
            )

        status, _ = _run_json(
            probe=probe,
            cwd=root,
            args=["status"],
            timeout=timeout,
            env_overrides=leader_env,
        )
        _assert(checks, status["summary"]["total"] == 2, "status:goal-count", status["summary"])
        _assert(
            checks, status["summary"]["pending"] == 2, "status:initial-pending", status["summary"]
        )

        first_start, _ = _run_json(
            probe=probe,
            cwd=root,
            args=["complete-goals"],
            timeout=timeout,
            env_overrides=leader_env,
        )
        first_status, _ = _run_json(
            probe=probe,
            cwd=root,
            args=["status"],
            timeout=timeout,
            env_overrides=leader_env,
        )
        first_id = first_start.get("goal", {}).get("id")
        aggregate_objective = first_status["plan"].get("codexObjective")
        _assert(checks, bool(first_id), "story:first-active-id", first_id)
        _assert(checks, bool(aggregate_objective), "story:aggregate-objective", aggregate_objective)
        _assert(
            checks,
            first_status["summary"]["inProgress"] == 1,
            "story:first-started",
            first_status["summary"],
        )

        first_checkpoint, _ = _run_json(
            probe=probe,
            cwd=root,
            args=[
                "checkpoint",
                "--goal-id",
                str(first_id),
                "--status",
                "complete",
                "--evidence",
                "synthetic deterministic verification passed",
                "--codex-goal-json",
                json.dumps({"goal": {"objective": aggregate_objective, "status": "active"}}),
            ],
            timeout=timeout,
            env_overrides=leader_env,
        )
        _assert(
            checks,
            first_checkpoint["summary"]["complete"] == 1,
            "checkpoint:first-complete",
            first_checkpoint["summary"],
        )
        _assert(
            checks,
            first_checkpoint["summary"]["pending"] == 1,
            "checkpoint:second-pending",
            first_checkpoint["summary"],
        )

        second_start, _ = _run_json(
            probe=probe,
            cwd=root,
            args=["complete-goals"],
            timeout=timeout,
            env_overrides=leader_env,
        )
        second_id = second_start.get("goal", {}).get("id")
        _assert(
            checks,
            bool(second_id) and second_id != first_id,
            "story:second-started",
            second_id,
        )

        blocked, _ = _run_json(
            probe=probe,
            cwd=root,
            args=[
                "checkpoint",
                "--goal-id",
                str(second_id),
                "--status",
                "blocked",
                "--evidence",
                "completed foreign Codex goal blocks the next synthetic story",
                "--codex-goal-json",
                json.dumps(
                    {
                        "goal": {
                            "objective": "Foreign completed objective from a prior run.",
                            "status": "complete",
                        }
                    }
                ),
            ],
            timeout=timeout,
            env_overrides=leader_env,
        )
        _assert(
            checks,
            blocked["summary"]["inProgress"] == 1,
            "checkpoint:blocker-is-non-terminal",
            blocked["summary"],
        )
        _assert(
            checks,
            blocked["plan"].get("activeGoalId") == second_id,
            "checkpoint:blocker-retains-active-story",
            blocked["plan"].get("activeGoalId"),
        )

        ledger_lines = _read_ledger(root)
        ledger_events = [entry.get("event") for entry in ledger_lines]
        expected_events = [
            "plan_created",
            "goal_started",
            "goal_completed",
            "goal_started",
            "goal_blocked",
        ]
        _assert(
            checks,
            ledger_events == expected_events,
            "ledger:event-sequence",
            {"expected": expected_events, "actual": ledger_events},
        )

        worker_root = root / "worker-guard"
        worker_root.mkdir()
        worker_brief = worker_root / "brief.md"
        worker_brief.write_text("- A Team worker must not create this goal.\n", encoding="utf-8")
        worker_run = omx_adapter.run_bounded(
            [
                str(probe["cli_path"]),
                "ultragoal",
                "create-goals",
                "--brief-file",
                str(worker_brief),
                "--json",
            ],
            cwd=worker_root,
            timeout=timeout,
            env_overrides={
                "OMX_TEAM_WORKER": "integration-probe/worker-1",
                "OMX_TEAM_INTERNAL_WORKER": None,
            },
        )
        worker_output = f"{worker_run['stdout']}\n{worker_run['stderr']}"
        _assert(
            checks,
            not worker_run["timed_out"] and worker_run["returncode"] != 0,
            "worker-guard:mutation-rejected",
            worker_run,
        )
        _assert(
            checks,
            "leader-owned" in worker_output,
            "worker-guard:leader-ownership-message",
            worker_output,
        )
        _assert(
            checks,
            not (worker_root / ".omx/ultragoal/goals.json").exists(),
            "worker-guard:no-runtime-artifacts",
            str(worker_root),
        )

        checks.extend(
            run_structured_steering_integration(
                probe=probe,
                parent=root,
                timeout=timeout,
                env_overrides=leader_env,
            )
        )

    return {
        "status": "PASS",
        "message": "Audited OMX temporary-repository integration flow passed.",
        "audited_contract": omx_adapter.audited_contract(),
        "checks": checks,
        "temporary_artifacts_retained": False,
    }


def emit(report: Mapping[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{report['status']}: {report['message']}")
        if report.get("checks"):
            print(f"Checks: {sum(1 for check in report['checks'] if check.get('ok'))}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a bounded, hermetic OMX v0.20.3 Ultragoal integration test. "
            "Unavailable or unsupported OMX is reported as SKIP unless explicitly required."
        )
    )
    parser.add_argument("--omx-command", default="omx", help="OMX executable name or path")
    parser.add_argument("--timeout", type=int, default=20, help="per-command timeout in seconds")
    parser.add_argument(
        "--require-omx",
        action="store_true",
        help="report FAIL rather than SKIP when the compatible external tool is unavailable",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    try:
        timeout_checks = run_timeout_regression()
    except Exception as exc:
        report = {
            "status": "FAIL",
            "message": (f"OMX subprocess timeout regression failed: {type(exc).__name__}: {exc}"),
            "checks": [],
        }
        emit(report, as_json=args.json)
        return 1

    probe = omx_adapter.probe_omx(args.omx_command, timeout=args.timeout)
    if probe["status"] != "PASS":
        if args.require_omx:
            report = {
                "status": "FAIL",
                "message": (
                    "Compatible OMX was explicitly required, but the integration probe "
                    f"reported {probe['status']} ({probe['reason_code']})."
                ),
                "probe": probe,
                "checks": timeout_checks,
            }
        else:
            report = {
                "status": "SKIP",
                "message": (
                    "OMX integration was not run because the audited external interface "
                    f"is unavailable ({probe['reason_code']})."
                ),
                "probe": probe,
                "checks": timeout_checks,
            }
        emit(report, as_json=args.json)
        return 1 if report["status"] == "FAIL" else 0

    try:
        report = run_integration(probe, timeout=args.timeout)
        report["checks"] = [*timeout_checks, *report["checks"]]
    except Exception as exc:
        report = {
            "status": "FAIL",
            "message": f"OMX integration failed: {type(exc).__name__}: {exc}",
            "probe": probe,
            "checks": timeout_checks,
        }
    emit(report, as_json=args.json)
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
