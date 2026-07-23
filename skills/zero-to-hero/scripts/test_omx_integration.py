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

        ledger_lines = [
            json.loads(line)
            for line in (root / ".omx/ultragoal/ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
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
