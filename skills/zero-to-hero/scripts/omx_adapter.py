#!/usr/bin/env python3
"""Probe and, when explicitly requested, invoke the audited OMX Ultragoal CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

sys.dont_write_bytecode = True

AUDITED_VERSION = "0.20.3"
AUDITED_RANGE = "==0.20.3"
AUDITED_TAG = "v0.20.3"
AUDITED_COMMIT = "6c970cc12da256bfc7667edd0a9183b158d4a7a7"
AUDITED_DATE = "2026-07-23"
RUNTIME_ARTIFACTS = (
    ".omx/ultragoal/brief.md",
    ".omx/ultragoal/goals.json",
    ".omx/ultragoal/ledger.jsonl",
)
STEERING_MUTATION_KINDS = (
    "add_subgoal",
    "split_subgoal",
    "reorder_pending",
    "revise_pending_wording",
    "annotate_ledger",
    "mark_blocked_superseded",
)
STEERING_SOURCES = ("cli", "finding", "user_prompt_submit")
STEERING_EXECUTABLE_FLAGS = (
    "--kind",
    "--source",
    "--evidence",
    "--rationale",
    "--target-goal-id",
    "--title",
    "--objective",
    "--after-json",
    "--idempotency-key",
    "--directive-json",
    "--json",
)
STEERING_ADVERTISED_ONLY_FLAGS = ("--target-goal-ids",)
STEERING_LEDGER_EVENTS = ("steering_accepted", "steering_rejected")
REQUIRED_HELP_TOKENS = (
    "omx ultragoal create-goals",
    "--brief-file <path>",
    "--codex-goal-mode <aggregate|per-story>",
    "omx ultragoal complete-goals",
    "omx ultragoal steer --kind <mutation-kind>",
    "--target-goal-id <id>",
    (
        "omx ultragoal steer --kind "
        "<add_subgoal|split_subgoal|reorder_pending|revise_pending_wording|"
        "annotate_ledger|mark_blocked_superseded>"
    ),
    "--after-json <json-or-path>",
    "--idempotency-key <key>",
    "omx ultragoal steer --directive-json <json-or-path>",
    "omx ultragoal record-review-blockers",
    "omx ultragoal checkpoint",
    "--status <complete|failed|blocked>",
    "--codex-goal-json <json-or-path>",
    "--quality-gate-json <json-or-path>",
    "omx ultragoal status",
    "Ultragoal does not call /goal clear",
    "multiple sequential ultragoal runs in one Codex session/thread, manually run",
    "/goal clear in the Codex UI before creating the next aggregate goal.",
    "Dynamic steering is explicit-only",
    "audits accepted/rejected/deduped results in .omx/ultragoal/ledger.jsonl",
    "rejects broad natural-language mutation requests.",
    *RUNTIME_ARTIFACTS,
)
VERSION_PATTERN = re.compile(r"(?m)^oh-my-codex v(?P<version>\d+\.\d+\.\d+(?:[-+][^\s]+)?)\s*$")
TERMINATION_GRACE_SECONDS = 0.5
OUTPUT_DRAIN_SECONDS = 1.0


def audited_contract() -> dict[str, Any]:
    return {
        "tested_compatibility_range": AUDITED_RANGE,
        "version": AUDITED_VERSION,
        "tag": AUDITED_TAG,
        "commit": AUDITED_COMMIT,
        "audited_date": AUDITED_DATE,
        "required_help_tokens": list(REQUIRED_HELP_TOKENS),
        "runtime_owned_artifacts": list(RUNTIME_ARTIFACTS),
        "structured_steering": {
            "mutation_kinds": list(STEERING_MUTATION_KINDS),
            "sources": list(STEERING_SOURCES),
            "executable_cli_flags": list(STEERING_EXECUTABLE_FLAGS),
            "advertised_only_cli_flags": list(STEERING_ADVERTISED_ONLY_FLAGS),
            "ledger_events": list(STEERING_LEDGER_EVENTS),
            "outcomes": ["accepted", "rejected", "deduped"],
            "dedupe_contract": (
                "An accepted idempotency-key replay returns the prior accepted audit with "
                "deduped=true and does not append a second ledger event."
            ),
            "reorder_payload_field": "after.pendingGoalIds",
        },
        "same_thread_aggregate_cleanup": {
            "required_ui_command": "/goal clear",
            "when": (
                "after a completed aggregate Ultragoal run and before create_goal for "
                "another OMX goal in the same Codex thread/session"
            ),
            "omx_invokes_clear": False,
        },
    }


def neutral_fallback(reason: str) -> dict[str, Any]:
    return {
        "required": True,
        "reason": reason,
        "runtime_artifacts_created": False,
        "action": (
            "Retain the neutral implementation brief and approved planning evidence. "
            "Use native Codex planning and scoped subagents, or a deterministic sequential "
            "execution plan; do not fabricate OMX runtime artifacts."
        ),
    }


def _text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _process_isolation() -> tuple[dict[str, Any], str]:
    if os.name == "posix":
        return {"start_new_session": True}, "posix_session"
    if os.name == "nt":
        creation_flag = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if creation_flag:
            return {"creationflags": creation_flag}, "windows_process_group"
    return {}, "direct_process_only"


def _wait_for_exit(process: subprocess.Popen[str], timeout: float) -> bool:
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    return True


def _terminate_bounded_process(process: subprocess.Popen[str]) -> dict[str, Any]:
    """Stop a timed-out command and its descendants where stdlib primitives allow."""

    actions: list[str] = []
    errors: list[str] = []
    tree_termination = "direct_process_only"

    if os.name == "posix" and hasattr(os, "killpg"):
        tree_termination = "posix_process_group"
        try:
            os.killpg(process.pid, signal.SIGTERM)
            actions.append("process_group_sigterm")
        except ProcessLookupError:
            actions.append("process_group_already_exited")
        except OSError as exc:
            errors.append(f"process_group_sigterm:{type(exc).__name__}:{exc}")
            if process.poll() is None:
                try:
                    process.terminate()
                    actions.append("direct_process_terminate_fallback")
                except OSError as fallback_exc:
                    errors.append(
                        "direct_process_terminate_fallback:"
                        f"{type(fallback_exc).__name__}:{fallback_exc}"
                    )

        _wait_for_exit(process, TERMINATION_GRACE_SECONDS)
        # Escalate the group even when its leader exited after SIGTERM: a descendant
        # may ignore SIGTERM while retaining the isolated process-group identifier.
        try:
            os.killpg(process.pid, signal.SIGKILL)
            actions.append("process_group_sigkill")
        except ProcessLookupError:
            actions.append("process_group_exited_before_sigkill")
        except OSError as exc:
            errors.append(f"process_group_sigkill:{type(exc).__name__}:{exc}")
            if process.poll() is None:
                try:
                    process.kill()
                    actions.append("direct_process_kill_fallback")
                except OSError as fallback_exc:
                    errors.append(
                        f"direct_process_kill_fallback:{type(fallback_exc).__name__}:{fallback_exc}"
                    )
    elif os.name == "nt":
        tree_termination = "windows_process_group_best_effort"
        ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", None)
        if ctrl_break is not None:
            try:
                process.send_signal(ctrl_break)
                actions.append("process_group_ctrl_break")
            except OSError as exc:
                errors.append(f"process_group_ctrl_break:{type(exc).__name__}:{exc}")
        _wait_for_exit(process, TERMINATION_GRACE_SECONDS)
        if process.poll() is None:
            try:
                process.terminate()
                actions.append("direct_process_terminate")
            except OSError as exc:
                errors.append(f"direct_process_terminate:{type(exc).__name__}:{exc}")
        _wait_for_exit(process, TERMINATION_GRACE_SECONDS)
        if process.poll() is None:
            try:
                process.kill()
                actions.append("direct_process_kill")
            except OSError as exc:
                errors.append(f"direct_process_kill:{type(exc).__name__}:{exc}")
    else:
        if process.poll() is None:
            try:
                process.terminate()
                actions.append("direct_process_terminate")
            except OSError as exc:
                errors.append(f"direct_process_terminate:{type(exc).__name__}:{exc}")
        _wait_for_exit(process, TERMINATION_GRACE_SECONDS)
        if process.poll() is None:
            try:
                process.kill()
                actions.append("direct_process_kill")
            except OSError as exc:
                errors.append(f"direct_process_kill:{type(exc).__name__}:{exc}")

    direct_process_exited = _wait_for_exit(process, OUTPUT_DRAIN_SECONDS)
    return {
        "strategy": tree_termination,
        "actions": actions,
        "errors": errors,
        "direct_process_exited": direct_process_exited,
        "direct_process_returncode": process.returncode,
    }


def run_bounded(
    command: Sequence[str],
    *,
    cwd: Path | None,
    timeout: float,
    env_overrides: Mapping[str, str | None] | None = None,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for key, value in (env_overrides or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    isolation_kwargs, isolation = _process_isolation()
    try:
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            **isolation_kwargs,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            termination = _terminate_bounded_process(process)
            try:
                stdout, stderr = process.communicate(timeout=OUTPUT_DRAIN_SECONDS)
            except subprocess.TimeoutExpired as drain_exc:
                stdout = _text(drain_exc.stdout) or _text(exc.stdout)
                stderr = _text(drain_exc.stderr) or _text(exc.stderr)
                for pipe in (process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()
            return {
                "command": list(command),
                "returncode": None,
                "stdout": _text(stdout),
                "stderr": _text(stderr),
                "timed_out": True,
                "timeout_seconds": timeout,
                "process_isolation": isolation,
                "termination": termination,
            }
        return {
            "command": list(command),
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": False,
            "process_isolation": isolation,
        }
    except OSError as exc:
        return {
            "command": list(command),
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
            "launch_error": type(exc).__name__,
            "process_isolation": isolation,
        }


def _skip(reason_code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": "SKIP",
        "compatible": False,
        "reason_code": reason_code,
        "message": message,
        "audited_contract": audited_contract(),
        "neutral_fallback": neutral_fallback(message),
        **extra,
    }


def _fail(reason_code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "compatible": False,
        "reason_code": reason_code,
        "message": message,
        "audited_contract": audited_contract(),
        **extra,
    }


def probe_omx(
    omx_command: str = "omx",
    *,
    timeout: int = 10,
    env_overrides: Mapping[str, str | None] | None = None,
) -> dict[str, Any]:
    """Perform a read-only version and interface probe.

    Missing, unaudited, or interface-incompatible OMX installations are SKIP results.
    Callers that explicitly require OMX must promote SKIP to FAIL.
    """

    executable = shutil.which(omx_command)
    if executable is None:
        return _skip("omx_not_found", f"OMX command {omx_command!r} was not found.")

    version_run = run_bounded(
        [executable, "--version"],
        cwd=None,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    if version_run["timed_out"]:
        return _skip(
            "version_probe_timeout",
            f"OMX version probe timed out after {timeout} seconds.",
            cli_path=executable,
            version_probe=version_run,
        )
    if version_run["returncode"] != 0:
        return _skip(
            "version_probe_failed",
            "OMX is installed but its version probe failed.",
            cli_path=executable,
            version_probe=version_run,
        )

    version_output = f"{version_run['stdout']}\n{version_run['stderr']}"
    version_match = VERSION_PATTERN.search(version_output)
    if version_match is None:
        return _skip(
            "version_unrecognized",
            "OMX version output did not match the audited oh-my-codex format.",
            cli_path=executable,
            version_probe=version_run,
        )

    detected_version = version_match.group("version")
    if detected_version != AUDITED_VERSION:
        return _skip(
            "version_unsupported",
            (
                f"Detected oh-my-codex v{detected_version}; this adapter has only been "
                f"audited for {AUDITED_RANGE}."
            ),
            cli_path=executable,
            detected_version=detected_version,
            version_probe=version_run,
        )

    help_run = run_bounded(
        [executable, "ultragoal", "--help"],
        cwd=None,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    if help_run["timed_out"]:
        return _skip(
            "interface_probe_timeout",
            f"OMX Ultragoal interface probe timed out after {timeout} seconds.",
            cli_path=executable,
            detected_version=detected_version,
            version_probe=version_run,
            interface_probe=help_run,
        )
    if help_run["returncode"] != 0:
        return _skip(
            "interface_probe_failed",
            "OMX is installed at the audited version but its Ultragoal help probe failed.",
            cli_path=executable,
            detected_version=detected_version,
            version_probe=version_run,
            interface_probe=help_run,
        )

    help_output = f"{help_run['stdout']}\n{help_run['stderr']}"
    missing_tokens = [token for token in REQUIRED_HELP_TOKENS if token not in help_output]
    if missing_tokens:
        return _skip(
            "interface_unsupported",
            "The installed OMX Ultragoal interface is missing audited commands or options.",
            cli_path=executable,
            detected_version=detected_version,
            missing_help_tokens=missing_tokens,
            version_probe=version_run,
            interface_probe=help_run,
        )

    return {
        "status": "PASS",
        "compatible": True,
        "reason_code": "compatible",
        "message": (
            f"Detected oh-my-codex v{detected_version} with the audited Ultragoal interface."
        ),
        "cli_path": executable,
        "detected_version": detected_version,
        "audited_contract": audited_contract(),
        "interface": {
            "probe_command": [executable, "ultragoal", "--help"],
            "missing_help_tokens": [],
        },
        "neutral_fallback": None,
    }


def require_compatible(probe: Mapping[str, Any], requested_action: str) -> dict[str, Any]:
    if probe.get("status") == "PASS" and probe.get("compatible") is True:
        return dict(probe)
    return _fail(
        "compatible_omx_required",
        (
            f"Cannot {requested_action}: a compatible OMX {AUDITED_RANGE} interface was "
            f"explicitly required, but the probe reported {probe.get('status', 'UNKNOWN')} "
            f"({probe.get('reason_code', 'unknown')})."
        ),
        probe=dict(probe),
        neutral_fallback=neutral_fallback(str(probe.get("message", "OMX is unavailable."))),
    )


def execute_create_goals(
    *,
    repo: Path,
    brief_file: Path,
    probe: Mapping[str, Any],
    timeout: int = 20,
    env_overrides: Mapping[str, str | None] | None = None,
) -> dict[str, Any]:
    """Let the compatible OMX CLI create its own Ultragoal artifacts.

    This deliberately does not expose or pass ``--force``.
    """

    compatible = require_compatible(probe, "create Ultragoal artifacts")
    if compatible["status"] != "PASS":
        return compatible

    target_repo = repo.resolve()
    source_brief = brief_file.resolve()
    if not target_repo.is_dir():
        return _fail(
            "target_repo_invalid",
            f"Target repository directory does not exist: {target_repo}",
            probe=dict(probe),
        )
    if not source_brief.is_file():
        return _fail(
            "brief_file_invalid",
            f"Neutral implementation brief does not exist: {source_brief}",
            probe=dict(probe),
        )
    existing_artifacts = [
        relative for relative in RUNTIME_ARTIFACTS if (target_repo / relative).exists()
    ]
    if existing_artifacts:
        return _fail(
            "runtime_artifacts_exist",
            (
                "Refusing to invoke create-goals because OMX runtime artifacts already "
                "exist; inspect the current run instead of overwriting it."
            ),
            probe=dict(probe),
            existing_artifacts=existing_artifacts,
        )

    cli_path = probe.get("cli_path")
    if not isinstance(cli_path, str) or not cli_path:
        return _fail(
            "compatible_probe_invalid",
            "Compatible probe result did not include an OMX executable path.",
            probe=dict(probe),
        )

    command = [
        cli_path,
        "ultragoal",
        "create-goals",
        "--brief-file",
        str(source_brief),
        "--json",
    ]
    run = run_bounded(
        command,
        cwd=target_repo,
        timeout=timeout,
        env_overrides=env_overrides,
    )
    if run["timed_out"]:
        return _fail(
            "create_goals_timeout",
            f"OMX create-goals timed out after {timeout} seconds.",
            probe=dict(probe),
            execution=run,
        )
    if run["returncode"] != 0:
        return _fail(
            "create_goals_failed",
            "OMX create-goals failed; no fallback artifacts were fabricated.",
            probe=dict(probe),
            execution=run,
        )

    try:
        payload = json.loads(run["stdout"])
    except json.JSONDecodeError as exc:
        return _fail(
            "create_goals_invalid_json",
            f"OMX create-goals returned invalid JSON: {exc}",
            probe=dict(probe),
            execution=run,
        )
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return _fail(
            "create_goals_not_ok",
            "OMX create-goals did not report ok=true.",
            probe=dict(probe),
            execution=run,
            omx_payload=payload,
        )

    plan = payload.get("plan")
    declared_artifacts = (
        [plan.get("briefPath"), plan.get("goalsPath"), plan.get("ledgerPath")]
        if isinstance(plan, dict)
        else []
    )
    if declared_artifacts != list(RUNTIME_ARTIFACTS):
        return _fail(
            "runtime_artifact_contract_mismatch",
            "OMX returned runtime artifact paths that do not match the audited contract.",
            probe=dict(probe),
            execution=run,
            omx_payload=payload,
            expected_artifacts=list(RUNTIME_ARTIFACTS),
            declared_artifacts=declared_artifacts,
        )

    missing_artifacts = [
        relative for relative in RUNTIME_ARTIFACTS if not (target_repo / relative).is_file()
    ]
    if missing_artifacts:
        return _fail(
            "runtime_artifacts_missing",
            "OMX reported success but did not create every audited runtime artifact.",
            probe=dict(probe),
            execution=run,
            omx_payload=payload,
            missing_artifacts=missing_artifacts,
        )

    return {
        "status": "PASS",
        "compatible": True,
        "reason_code": "create_goals_complete",
        "message": "Compatible OMX CLI created and owns the Ultragoal runtime artifacts.",
        "probe": dict(probe),
        "execution": {
            "command": command,
            "returncode": run["returncode"],
            "omx_payload": payload,
        },
        "repo": str(target_repo),
        "brief_file": str(source_brief),
        "runtime_artifacts": [str(target_repo / path) for path in RUNTIME_ARTIFACTS],
        "neutral_fallback": None,
    }


def emit(report: Mapping[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2))
        return
    print(f"{report.get('status', 'FAIL')}: {report.get('message', 'No result message.')}")
    fallback = report.get("neutral_fallback")
    if isinstance(fallback, Mapping) and fallback.get("required"):
        print(f"Fallback: {fallback.get('action')}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe the audited OMX v0.20.3 Ultragoal interface and optionally let "
            "that CLI create runtime-owned goal artifacts."
        )
    )
    parser.add_argument("repo", nargs="?", default=".", help="target repository")
    parser.add_argument("--omx-command", default="omx", help="OMX executable name or path")
    parser.add_argument("--timeout", type=int, default=20, help="per-command timeout in seconds")
    parser.add_argument(
        "--require-compatible",
        action="store_true",
        help="fail instead of skip when the audited OMX interface is unavailable",
    )
    parser.add_argument(
        "--create-goals",
        action="store_true",
        help="explicitly authorize `omx ultragoal create-goals --brief-file ...`",
    )
    parser.add_argument("--brief-file", type=Path, help="neutral implementation brief")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if args.create_goals and args.brief_file is None:
        parser.error("--create-goals requires --brief-file")
    if args.brief_file is not None and not args.create_goals:
        parser.error("--brief-file requires --create-goals")

    probe = probe_omx(args.omx_command, timeout=args.timeout)
    if args.create_goals:
        report = execute_create_goals(
            repo=Path(args.repo),
            brief_file=args.brief_file,
            probe=probe,
            timeout=args.timeout,
        )
    elif args.require_compatible:
        report = require_compatible(probe, "use the OMX adapter")
    else:
        report = probe

    emit(report, as_json=args.json)
    return 1 if report.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
