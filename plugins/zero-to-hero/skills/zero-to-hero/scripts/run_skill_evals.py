#!/usr/bin/env python3
"""Run bounded external behavior evaluations for the zero-to-hero skill."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

PASS = "PASS"
SKIP = "SKIP"
FAIL = "FAIL"
TEXT_SUFFIXES = {".json", ".md", ".toml", ".txt", ".yaml", ".yml"}
RUBRIC_WEIGHTS = {
    "target_specificity": 15,
    "commands_and_harness": 20,
    "phase_and_ownership": 15,
    "profile_artifacts": 15,
    "evidence_and_done": 15,
    "safety_boundaries": 15,
    "unresolved_risks": 5,
}
RUBRIC_IDS = set(RUBRIC_WEIGHTS)
REQUIRED_RUBRIC_PASSES = {
    "commands_and_harness",
    "evidence_and_done",
    "safety_boundaries",
}
SKILL_EVENT_TYPES = {"skill", "skill_call", "skill_invocation"}
SKILL_PATH_MARKER = ".agents/skills/zero-to-hero/"
SKILL_NAMES = {"zero-to-hero", "$zero-to-hero"}
CASE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SKILL_READ_COMMAND = re.compile(
    r"^\s*(?:cat|sed|head|tail|less|more|bat|type|"
    r"get-content|grep|rg|awk)\b",
    re.IGNORECASE,
)
UNAVAILABLE_STDERR_PATTERNS = (
    re.compile(r"\bmissing optional dependency\b", re.IGNORECASE),
    re.compile(r"\bnot logged in\b", re.IGNORECASE),
    re.compile(r"\blogin required\b", re.IGNORECASE),
    re.compile(r"\bauthentication required\b", re.IGNORECASE),
    re.compile(r"\b(?:401|403)\s+(?:unauthorized|forbidden)\b", re.IGNORECASE),
    re.compile(r"\brate limit(?:ed| exceeded)?\b", re.IGNORECASE),
    re.compile(r"\b(?:connection refused|failed to connect|unable to connect)\b", re.IGNORECASE),
)


@dataclass
class CommandResult:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    seconds: float
    spawn_error: str | None = None


def resolve_skill(path_arg: str | None) -> Path:
    root = Path(path_arg or ".").resolve()
    if (root / "SKILL.md").exists():
        return root
    candidate = root / ".agents" / "skills" / "zero-to-hero"
    if (candidate / "SKILL.md").exists():
        return candidate
    return root


def tail(text: str, limit: int = 2000) -> str:
    return text[-limit:]


def run_bounded(
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str],
) -> CommandResult:
    start = time.monotonic()
    kwargs: dict[str, Any] = {}
    if os.name == "posix":
        kwargs["start_new_session"] = True
    elif hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kwargs,
        )
    except OSError as exc:
        return CommandResult(
            None,
            "",
            str(exc),
            False,
            round(time.monotonic() - start, 3),
            spawn_error=str(exc),
        )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return CommandResult(
            process.returncode,
            stdout,
            stderr,
            False,
            round(time.monotonic() - start, 3),
        )
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        stdout, stderr = process.communicate()
        return CommandResult(
            process.returncode,
            stdout,
            stderr,
            True,
            round(time.monotonic() - start, 3),
        )


def load_suite(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "zero-to-hero.skill-evals.v1":
        raise ValueError(f"unsupported eval schema in {path}")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("eval suite must contain at least one case")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("every eval case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or CASE_ID_PATTERN.fullmatch(case_id) is None:
            raise ValueError(
                "every eval case id must be a portable lowercase slug "
                "(letters, digits, dot, underscore, or hyphen; maximum 128 characters)"
            )
        if case_id in seen:
            raise ValueError(f"duplicate eval case id: {case_id}")
        seen.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError(f"{case_id}: prompt must be a non-empty string")
        if case.get("sandbox") not in {"read-only", "workspace-write"}:
            raise ValueError(f"{case_id}: unsupported sandbox")
        if not isinstance(case.get("should_invoke"), bool):
            raise ValueError(f"{case_id}: should_invoke must be boolean")
        if not isinstance(case.get("category"), str) or not case["category"]:
            raise ValueError(f"{case_id}: category must be a non-empty string")
        setup_files = case.get("setup_files", {})
        if not isinstance(setup_files, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in setup_files.items()
        ):
            raise ValueError(f"{case_id}: setup_files must map paths to text")
        checks = case.get("checks", {})
        if not isinstance(checks, dict):
            raise ValueError(f"{case_id}: checks must be an object")
    return data


def probe_codex(
    executable_arg: str,
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str],
) -> dict[str, Any]:
    executable = shutil.which(executable_arg)
    if executable is None:
        candidate = Path(executable_arg)
        if candidate.exists():
            executable = str(candidate.resolve())
    if executable is None:
        return {
            "status": SKIP,
            "reason": f"Codex executable not found: {executable_arg}",
        }

    version = run_bounded([executable, "--version"], cwd=cwd, timeout=timeout, env=env)
    if version.timed_out or version.returncode != 0:
        return {
            "status": SKIP,
            "reason": "Codex executable exists but is not operational",
            "executable": executable,
            "stdout_tail": tail(version.stdout),
            "stderr_tail": tail(version.stderr),
        }

    help_result = run_bounded(
        [executable, "exec", "--help"],
        cwd=cwd,
        timeout=timeout,
        env=env,
    )
    if help_result.timed_out or help_result.returncode != 0:
        return {
            "status": SKIP,
            "reason": "codex exec is unavailable",
            "executable": executable,
            "version": version.stdout.strip(),
            "stderr_tail": tail(help_result.stderr),
        }
    required_flags = {"--json", "--sandbox", "--cd", "--skip-git-repo-check"}
    missing_flags = sorted(flag for flag in required_flags if flag not in help_result.stdout)
    if missing_flags:
        return {
            "status": SKIP,
            "reason": "codex exec lacks required automation flags",
            "executable": executable,
            "version": version.stdout.strip(),
            "missing_flags": missing_flags,
        }
    return {
        "status": PASS,
        "executable": executable,
        "version": version.stdout.strip(),
        "supports_ephemeral": "--ephemeral" in help_result.stdout,
        "supports_ignore_user_config": "--ignore-user-config" in help_result.stdout,
        "supports_approval_policy": "--ask-for-approval" in help_result.stdout,
        "supports_output_schema": "--output-schema" in help_result.stdout,
        "supports_output_last_message": "--output-last-message" in help_result.stdout,
    }


def write_setup_files(workspace: Path, setup_files: dict[str, str]) -> None:
    for relative, content in setup_files.items():
        path = (workspace / relative).resolve()
        try:
            path.relative_to(workspace.resolve())
        except ValueError as exc:
            raise ValueError(f"setup file escapes workspace: {relative}") from exc
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def ignored_snapshot_path(relative: Path) -> bool:
    return any(part in {".codex", ".git", "__pycache__"} for part in relative.parts)


def hash_tree(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ignored_snapshot_path(relative):
            continue
        if path.is_symlink():
            target = os.readlink(path)
            hashes[relative.as_posix()] = hashlib.sha256(f"symlink:{target}".encode()).hexdigest()
            continue
        if not path.is_file():
            continue
        hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def changed_paths(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return {path for path in set(before) | set(after) if before.get(path) != after.get(path)}


def created_paths(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return set(after) - set(before)


def glob_matches(path: str, pattern: str) -> bool:
    """Match slash-separated paths, allowing a globstar directory to be empty."""
    candidates = {pattern}
    pending = [pattern]
    while pending:
        candidate = pending.pop()
        marker = candidate.find("**/")
        while marker >= 0:
            without_empty_globstar = candidate[:marker] + candidate[marker + 3 :]
            if without_empty_globstar not in candidates:
                candidates.add(without_empty_globstar)
                pending.append(without_empty_globstar)
            marker = candidate.find("**/", marker + 3)
    return any(fnmatch.fnmatchcase(path, candidate) for candidate in candidates)


def paths_for_pattern(root: Path, pattern: str) -> list[str]:
    matches: list[str] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        if ignored_snapshot_path(path.relative_to(root)):
            continue
        relative = path.relative_to(root).as_posix()
        if glob_matches(relative, pattern):
            matches.append(relative)
    return sorted(matches)


def parse_jsonl(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: {exc}")
            continue
        if not isinstance(event, dict):
            errors.append(f"line {line_number}: JSONL event must be an object")
            continue
        events.append(event)
    if not events and not errors:
        errors.append("trace contains no JSONL events")
    return events, errors


def event_text(events: list[dict[str, Any]]) -> tuple[str, str, list[str]]:
    all_text: list[str] = []
    final_messages: list[str] = []
    commands: list[str] = []
    seen_command_ids: set[str] = set()
    for event in events:
        item = event.get("item")
        if isinstance(item, dict):
            item_type = item.get("type")
            command = item.get("command")
            if item_type == "command_execution" and isinstance(command, str):
                command_id = item.get("id")
                if not isinstance(command_id, str) or command_id not in seen_command_ids:
                    commands.append(command)
                    all_text.append(command)
                    if isinstance(command_id, str):
                        seen_command_ids.add(command_id)
            for key in ("text", "message", "output"):
                value = item.get(key)
                if isinstance(value, str):
                    all_text.append(value)
                    if item_type == "agent_message":
                        final_messages.append(value)
        message = event.get("message")
        if isinstance(message, str):
            all_text.append(message)
    return "\n".join(all_text), "\n".join(final_messages), commands


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [
            text
            for item in value
            for text in _string_values(item)
        ]
    if isinstance(value, dict):
        return [
            text
            for item in value.values()
            for text in _string_values(item)
        ]
    return []


def command_reads_skill_contract(command: str) -> bool:
    """Recognize a concrete content-read command for the repo-scoped skill."""

    normalized = command.replace("\\", "/").lower()
    if SKILL_PATH_MARKER not in normalized:
        return False
    segments = re.split(r"(?:&&|;|\|\|)", normalized)
    return any(
        SKILL_PATH_MARKER in segment and SKILL_READ_COMMAND.match(segment)
        for segment in segments
    )


def skill_invocation_evidence(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return trace records that deterministically show zero-to-hero was used."""

    evidence: list[dict[str, Any]] = []
    seen: set[tuple[int, str, str]] = set()
    for index, event in enumerate(events):
        records: list[tuple[str, dict[str, Any]]] = []
        item = event.get("item")
        if isinstance(item, dict):
            records.append(("item", item))
        if str(event.get("type", "")).lower() in SKILL_EVENT_TYPES:
            records.append(("event", event))

        for scope, record in records:
            record_type = str(record.get("type", "")).lower()
            candidates: list[tuple[str, str]] = []
            if record_type == "command_execution":
                candidates.extend(
                    ("command", value)
                    for value in _string_values(record.get("command"))
                    if command_reads_skill_contract(value)
                )
            elif record_type in SKILL_EVENT_TYPES:
                for field in ("name", "skill", "skill_name", "path", "input", "arguments"):
                    candidates.extend(
                        (field, value)
                        for value in _string_values(record.get(field))
                    )
            elif record_type in {"dynamic_tool_call", "mcp_tool_call", "tool_call"}:
                for field in ("name", "path", "input", "arguments"):
                    candidates.extend(
                        (field, value)
                        for value in _string_values(record.get(field))
                    )

            for field, value in candidates:
                normalized = value.replace("\\", "/").lower()
                exact_name = normalized.strip().strip("'\"") in SKILL_NAMES
                if SKILL_PATH_MARKER not in normalized and not (
                    record_type in SKILL_EVENT_TYPES and exact_name
                ):
                    continue
                key = (index, scope, field)
                if key in seen:
                    continue
                seen.add(key)
                evidence.append(
                    {
                        "event_index": index,
                        "scope": scope,
                        "type": record_type,
                        "field": field,
                        "value": tail(value, 500),
                    }
                )
    return evidence


def read_search_text(workspace: Path, patterns: list[str]) -> str:
    selected: set[Path] = set()
    for pattern in patterns:
        for path in workspace.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(workspace)
            if ignored_snapshot_path(relative):
                continue
            if glob_matches(relative.as_posix(), pattern):
                selected.add(path)
    chunks: list[str] = []
    for path in sorted(selected):
        if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 1024 * 1024:
            continue
        chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def ordered_markers_present(text: str, markers: list[str]) -> tuple[bool, str | None]:
    lowered = text.lower()
    cursor = 0
    for marker in markers:
        index = lowered.find(marker.lower(), cursor)
        if index < 0:
            return False, marker
        cursor = index + len(marker)
    return True, None


def deterministic_grade(
    case: dict[str, Any],
    workspace: Path,
    before: dict[str, str],
    after: dict[str, str],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    checks = case.get("checks") or {}
    trace_text, final_text, commands = event_text(events)
    artifact_text = read_search_text(workspace, checks.get("search_globs", []))
    combined_text = "\n".join([final_text, artifact_text])
    changed = changed_paths(before, after)
    created = created_paths(before, after)
    invocation_evidence = skill_invocation_evidence(events)
    results: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, details: Any = None) -> None:
        results.append({"id": check_id, "pass": bool(passed), "details": details})

    should_invoke = case["should_invoke"]
    add(
        "skill_invocation",
        bool(invocation_evidence) is should_invoke,
        {
            "expected": should_invoke,
            "observed": bool(invocation_evidence),
            "evidence": invocation_evidence,
        },
    )

    expected_all = checks.get("expected_all_paths", [])
    for pattern in expected_all:
        found = paths_for_pattern(workspace, pattern)
        add(f"expected_path:{pattern}", bool(found), {"found": found})

    expected_any = checks.get("expected_any_paths", [])
    if expected_any:
        found_by_pattern = {
            pattern: paths_for_pattern(workspace, pattern) for pattern in expected_any
        }
        add(
            "expected_any_path",
            any(found_by_pattern.values()),
            {"found": found_by_pattern},
        )

    forbidden_created = checks.get("forbidden_created_globs", [])
    for pattern in forbidden_created:
        found = sorted(path for path in created if glob_matches(path, pattern))
        add(f"forbidden_created:{pattern}", not found, {"found": found})

    protected = checks.get("protected_globs", [])
    for pattern in protected:
        found = sorted(path for path in changed if glob_matches(path, pattern))
        add(f"protected_unchanged:{pattern}", not found, {"changed": found})

    if checks.get("require_unchanged_workspace"):
        add("workspace_unchanged", not changed, {"changed": sorted(changed)})

    required_text = checks.get("required_text", [])
    for value in required_text:
        add(
            f"required_text:{value}",
            value.lower() in combined_text.lower(),
        )

    forbidden_terms = checks.get("forbidden_skill_evidence_terms", [])
    skill_evidence_text = "\n".join([trace_text, final_text])
    for value in forbidden_terms:
        add(
            f"forbidden_skill_evidence:{value}",
            value.lower() not in skill_evidence_text.lower(),
        )

    markers = checks.get("ordered_markers", [])
    if markers:
        source = final_text if checks.get("order_source") == "final" else combined_text
        passed, missing_marker = ordered_markers_present(source, markers)
        add(
            "phase_order",
            passed,
            {"markers": markers, "first_missing_or_out_of_order": missing_marker},
        )

    max_commands = int(checks.get("max_command_count", case.get("max_command_count", 80)))
    add(
        "command_count",
        len(commands) <= max_commands,
        {"actual": len(commands), "maximum": max_commands},
    )
    return {
        "status": PASS if all(item["pass"] for item in results) else FAIL,
        "checks": results,
        "changed_paths": sorted(changed),
        "created_paths": sorted(created),
        "command_count": len(commands),
        "final_message_tail": tail(final_text, 4000),
    }


def unavailable_result(result: CommandResult) -> bool:
    """Classify only known external transport/auth failures from stderr.

    Eval output is intentionally excluded: generated prose may legitimately
    contain words such as "network" or "authentication" and must not turn a
    product or compiler failure into a suite-wide skip.
    """

    return any(pattern.search(result.stderr) for pattern in UNAVAILABLE_STDERR_PATTERNS)


def base_exec_command(probe: dict[str, Any], workspace: Path, sandbox: str) -> list[str]:
    command = [
        probe["executable"],
        "exec",
        "--json",
        "--sandbox",
        sandbox,
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
    ]
    if probe.get("supports_ephemeral"):
        command.append("--ephemeral")
    if probe.get("supports_ignore_user_config"):
        command.append("--ignore-user-config")
    if probe.get("supports_approval_policy"):
        command.extend(["--ask-for-approval", "never"])
    return command


def validate_rubric_output(data: Any, minimum_score: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["rubric output must be an object"]
    if data.get("overall_pass") is not True:
        errors.append("rubric overall_pass is not true")
    score = data.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or score < minimum_score:
        errors.append(f"rubric score must be at least {minimum_score}")
    checks = data.get("checks")
    if not isinstance(checks, list):
        return errors + ["rubric checks must be an array"]
    by_id = {
        item.get("id"): item
        for item in checks
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if set(by_id) != RUBRIC_IDS:
        errors.append(
            "rubric check ids differ: "
            f"missing={sorted(RUBRIC_IDS - set(by_id))}, "
            f"extra={sorted(set(by_id) - RUBRIC_IDS)}"
        )
    computed_score = 0.0
    score_is_valid = True
    for check_id, weight in RUBRIC_WEIGHTS.items():
        item = by_id.get(check_id)
        if not isinstance(item, dict):
            score_is_valid = False
            continue
        criterion_score = item.get("score")
        if (
            not isinstance(criterion_score, int)
            or isinstance(criterion_score, bool)
            or not 0 <= criterion_score <= 4
        ):
            errors.append(f"invalid rubric criterion score: {check_id}")
            score_is_valid = False
            continue
        expected_pass = criterion_score >= 3
        if item.get("pass") is not expected_pass:
            errors.append(
                f"rubric pass flag disagrees with score for {check_id}: score={criterion_score}"
            )
        notes = item.get("notes")
        if not isinstance(notes, str) or not notes.strip():
            errors.append(f"rubric criterion has no notes: {check_id}")
        evidence = item.get("evidence")
        if (
            not isinstance(evidence, list)
            or not evidence
            or not all(isinstance(value, str) and value.strip() for value in evidence)
        ):
            errors.append(f"rubric criterion has no concrete evidence: {check_id}")
        computed_score += weight * criterion_score / 4
    if score_is_valid and isinstance(score, int) and not isinstance(score, bool):
        expected_score = math.floor(computed_score + 0.5)
        if score != expected_score:
            errors.append(
                f"rubric score is inconsistent: reported={score}, computed={expected_score}"
            )
    for check_id in REQUIRED_RUBRIC_PASSES:
        if by_id.get(check_id, {}).get("pass") is not True:
            errors.append(f"required rubric check did not pass: {check_id}")
    return errors


def run_model_grader(
    *,
    probe: dict[str, Any],
    workspace: Path,
    skill: Path,
    timeout: int,
    env: dict[str, str],
    minimum_score: int,
    grader_model: str | None,
) -> dict[str, Any]:
    if not probe.get("supports_output_schema") or not probe.get("supports_output_last_message"):
        return {
            "status": SKIP,
            "kind": "external_model",
            "reason": "codex exec lacks structured grader flags",
        }
    rubric = skill / "evals" / "handoff-quality-rubric.md"
    schema = skill / "evals" / "handoff-quality-rubric.schema.json"
    output = workspace / ".codex-eval-handoff-grade.json"
    prompt = (
        "Read the repository without modifying it. Grade its zero-to-hero implementation "
        "handoff using the rubric below. Cite concrete paths and commands. Do not infer "
        "missing evidence as present.\n\n" + rubric.read_text(encoding="utf-8")
    )
    command = base_exec_command(probe, workspace, "read-only")
    command.extend(["--output-schema", str(schema), "-o", str(output)])
    if grader_model:
        command.extend(["--model", grader_model])
    command.append(prompt)
    result = run_bounded(command, cwd=workspace, timeout=timeout, env=env)
    if result.spawn_error:
        return {
            "status": SKIP,
            "kind": "external_model",
            "reason": f"model grader could not start: {result.spawn_error}",
        }
    if result.timed_out:
        return {
            "status": FAIL,
            "kind": "external_model",
            "reason": f"model grader timed out after {timeout}s",
        }
    if result.returncode != 0:
        return {
            "status": SKIP if unavailable_result(result) else FAIL,
            "kind": "external_model",
            "reason": "model grader did not complete",
            "returncode": result.returncode,
            "stderr_tail": tail(result.stderr),
        }
    try:
        data = json.loads(output.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "status": FAIL,
            "kind": "external_model",
            "reason": f"invalid structured grader output: {exc}",
        }
    errors = validate_rubric_output(data, minimum_score)
    return {
        "status": PASS if not errors else FAIL,
        "kind": "external_model",
        "score": data.get("score"),
        "errors": errors,
        "result": data,
    }


def run_case(
    case: dict[str, Any],
    *,
    skill: Path,
    suite_defaults: dict[str, Any],
    probe: dict[str, Any],
    root: Path,
    timeout_override: int | None,
    env: dict[str, str],
    use_model_grader: bool,
    grader_model: str | None,
) -> dict[str, Any]:
    case_id = case["id"]
    workspace = root / "workspaces" / case_id
    trace_path = root / "traces" / f"{case_id}.jsonl"
    workspace.mkdir(parents=True, exist_ok=True)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    write_setup_files(workspace, case.get("setup_files", {}))
    skill_target = workspace / ".agents" / "skills" / "zero-to-hero"
    shutil.copytree(
        skill,
        skill_target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    before = hash_tree(workspace)
    timeout = int(
        timeout_override
        or case.get("timeout_seconds")
        or suite_defaults.get("timeout_seconds", 180)
    )
    case.setdefault("max_command_count", suite_defaults.get("max_command_count", 80))
    command = base_exec_command(probe, workspace, case["sandbox"])
    command.append(case["prompt"])
    result = run_bounded(command, cwd=workspace, timeout=timeout, env=env)
    trace_path.write_text(result.stdout, encoding="utf-8")
    base = {
        "id": case_id,
        "category": case["category"],
        "should_invoke": case["should_invoke"],
        "seconds": result.seconds,
        "trace": str(trace_path),
        "workspace": str(workspace),
    }
    if result.spawn_error:
        return base | {
            "status": SKIP,
            "skip_scope": "suite",
            "reason": f"codex exec could not start: {result.spawn_error}",
        }
    if result.timed_out:
        return base | {
            "status": FAIL,
            "reason": f"codex exec timed out after {timeout}s",
            "stderr_tail": tail(result.stderr),
        }
    if result.returncode != 0:
        return base | {
            "status": SKIP if unavailable_result(result) else FAIL,
            "skip_scope": "suite" if unavailable_result(result) else None,
            "reason": "codex exec did not complete",
            "returncode": result.returncode,
            "stdout_tail": tail(result.stdout),
            "stderr_tail": tail(result.stderr),
        }
    events, trace_errors = parse_jsonl(result.stdout)
    if trace_errors:
        return base | {
            "status": FAIL,
            "reason": "invalid codex exec JSONL trace",
            "trace_errors": trace_errors,
        }
    after = hash_tree(workspace)
    deterministic = deterministic_grade(case, workspace, before, after, events)
    model_grader: dict[str, Any] = {
        "status": SKIP,
        "kind": "external_model",
        "reason": "not required by this case",
    }
    if case.get("model_grader"):
        if not use_model_grader:
            model_grader = {
                "status": SKIP,
                "kind": "external_model",
                "reason": "model grader disabled by --no-model-grader",
            }
        elif deterministic["status"] == PASS:
            model_grader = run_model_grader(
                probe=probe,
                workspace=workspace,
                skill=skill_target,
                timeout=timeout,
                env=env,
                minimum_score=int(suite_defaults.get("model_grader_minimum_score", 80)),
                grader_model=grader_model,
            )
        else:
            model_grader = {
                "status": SKIP,
                "kind": "external_model",
                "reason": "deterministic checks failed; external grading was not run",
            }
    required_statuses = [deterministic["status"]]
    if case.get("model_grader") and use_model_grader:
        required_statuses.append(model_grader["status"])
    status = FAIL if FAIL in required_statuses else SKIP if SKIP in required_statuses else PASS
    return base | {
        "status": status,
        "event_count": len(events),
        "deterministic": deterministic,
        "model_grader": model_grader,
        "stderr_tail": tail(result.stderr),
    }


def emit(summary: dict[str, Any], require_codex: bool) -> int:
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["status"] == FAIL:
        return 1
    if summary["status"] == SKIP and require_codex:
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill",
        nargs="?",
        default=".",
        help="skill root or repo containing .agents/skills/zero-to-hero",
    )
    parser.add_argument("--cases", help="override eval case JSON")
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--codex", default=os.environ.get("ZERO_TO_HERO_CODEX", "codex"))
    parser.add_argument("--timeout", type=int, help="per Codex invocation timeout")
    parser.add_argument("--probe-timeout", type=int, default=10)
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--artifacts-dir")
    parser.add_argument("--no-model-grader", action="store_true")
    parser.add_argument("--grader-model")
    parser.add_argument("--require-codex", action="store_true")
    parser.add_argument("--list-cases", action="store_true")
    args = parser.parse_args()

    invalid_timeouts = [
        name
        for name, value in (
            ("--timeout", args.timeout),
            ("--probe-timeout", args.probe_timeout),
        )
        if value is not None and value < 1
    ]
    if invalid_timeouts:
        print(
            json.dumps(
                {
                    "status": FAIL,
                    "reason": "timeouts must be positive integers",
                    "arguments": invalid_timeouts,
                }
            )
        )
        return 1

    skill = resolve_skill(args.skill)
    if not (skill / "SKILL.md").exists():
        print(json.dumps({"status": FAIL, "reason": f"skill root not found: {skill}"}))
        return 1
    cases_path = Path(args.cases).resolve() if args.cases else skill / "evals" / "cases.json"
    try:
        suite = load_suite(cases_path)
    except Exception as exc:
        print(json.dumps({"status": FAIL, "reason": f"invalid eval suite: {exc}"}))
        return 1

    selected = suite["cases"]
    if args.case_ids:
        requested = set(args.case_ids)
        selected = [case for case in selected if case["id"] in requested]
        missing = sorted(requested - {case["id"] for case in selected})
        if missing:
            print(
                json.dumps({"status": FAIL, "reason": "unknown eval case ids", "missing": missing})
            )
            return 1
    if args.max_cases:
        if args.max_cases < 1:
            print(json.dumps({"status": FAIL, "reason": "--max-cases must be >= 1"}))
            return 1
        selected = selected[: args.max_cases]
    if args.list_cases:
        print(
            json.dumps(
                {
                    "status": PASS,
                    "schema": suite["schema"],
                    "cases": [
                        {
                            "id": case["id"],
                            "category": case["category"],
                            "should_invoke": case["should_invoke"],
                            "model_grader": bool(case.get("model_grader")),
                        }
                        for case in selected
                    ],
                },
                indent=2,
            )
        )
        return 0

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    probe = probe_codex(
        args.codex,
        cwd=skill,
        timeout=args.probe_timeout,
        env=env,
    )
    if probe["status"] != PASS:
        return emit(
            {
                "status": SKIP,
                "kind": "external_skill_eval",
                "reason": probe["reason"],
                "codex": probe,
                "cases_selected": [case["id"] for case in selected],
                "cases_run": 0,
            },
            args.require_codex,
        )

    temporary: tempfile.TemporaryDirectory | None = None
    if args.artifacts_dir:
        artifacts_parent = Path(args.artifacts_dir).resolve()
        artifacts_parent.mkdir(parents=True, exist_ok=True)
        artifacts_root = Path(tempfile.mkdtemp(prefix="run-", dir=artifacts_parent))
        retained = True
    else:
        temporary = tempfile.TemporaryDirectory(prefix="zero-to-hero-evals-")
        artifacts_root = Path(temporary.name)
        retained = False

    try:
        results: list[dict[str, Any]] = []
        for case in selected:
            try:
                result = run_case(
                    case,
                    skill=skill,
                    suite_defaults=suite.get("defaults", {}),
                    probe=probe,
                    root=artifacts_root,
                    timeout_override=args.timeout,
                    env=env,
                    use_model_grader=not args.no_model_grader,
                    grader_model=args.grader_model,
                )
            except Exception as exc:
                result = {
                    "id": case["id"],
                    "category": case["category"],
                    "should_invoke": case["should_invoke"],
                    "status": FAIL,
                    "reason": f"eval harness error: {type(exc).__name__}: {exc}",
                }
            results.append(result)
            if result["status"] == SKIP and result.get("skip_scope") == "suite":
                break
        statuses = [result["status"] for result in results]
        suite_status = (
            FAIL
            if FAIL in statuses
            else SKIP
            if SKIP in statuses or len(results) != len(selected)
            else PASS
        )
        summary = {
            "status": suite_status,
            "kind": "external_skill_eval",
            "codex": probe,
            "cases_selected": len(selected),
            "cases_run": len(results),
            "model_grading": "external codex exec rubric",
            "artifacts_retained": retained,
            "artifacts_dir": str(artifacts_root) if retained else None,
            "results": results,
        }
        return emit(summary, args.require_codex)
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
