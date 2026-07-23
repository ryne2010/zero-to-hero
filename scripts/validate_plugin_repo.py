#!/usr/bin/env python3
"""Authoritative release gate for the zero-to-hero skill and plugin.

The gate keeps hermetic repository checks separate from optional external-tool
integrations. External integrations may report SKIP when their executable is
unavailable or unsupported; a hermetic check may never be skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "zero-to-hero"
SKILL_SCRIPT = SKILL / "scripts"
StatusMode = Literal["returncode", "external-json"]


@dataclass(frozen=True)
class CheckSpec:
    name: str
    command: list[str]
    kind: Literal["hermetic", "external"] = "hermetic"
    status_mode: StatusMode = "returncode"
    timeout: int | None = None


@dataclass
class CheckResult:
    name: str
    kind: str
    status: Literal["passed", "skipped", "failed", "timeout"]
    seconds: float
    command: list[str]
    detail: str = ""
    stdout: str = ""
    stderr: str = ""


def clean_runtime_artifacts(root: Path) -> None:
    """Remove only Python caches under known repository-owned source trees."""

    for path in [root / "skills", root / "plugins", root / "scripts", root / "tests"]:
        if not path.exists():
            continue
        for cache in path.rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)
        for compiled in [*path.rglob("*.pyc"), *path.rglob("*.pyo")]:
            compiled.unlink(missing_ok=True)


def python_files() -> list[str]:
    paths: list[Path] = []
    for base in [SKILL_SCRIPT, REPO_ROOT / "scripts", REPO_ROOT / "tests"]:
        if base.exists():
            paths.extend(sorted(base.rglob("*.py")))
    return [str(path.relative_to(REPO_ROOT)) for path in paths]


def check_plan() -> list[CheckSpec]:
    py = sys.executable
    return [
        CheckSpec("python-compile", [py, "-m", "py_compile", *python_files()]),
        CheckSpec("python-static-analysis", ["ruff", "check", "scripts", "skills/zero-to-hero/scripts", "tests"]),
        CheckSpec(
            "schema-and-contract-graph",
            [py, str(SKILL_SCRIPT / "schema_validate.py"), str(SKILL), "--json"],
        ),
        CheckSpec(
            "generated-contract-views",
            [py, str(SKILL_SCRIPT / "sync_contract_views.py"), str(SKILL)],
        ),
        CheckSpec(
            "phase-gates",
            [py, str(SKILL_SCRIPT / "phase_gate_check.py"), str(SKILL)],
        ),
        CheckSpec(
            "prompt-contracts",
            [py, str(SKILL_SCRIPT / "prompt_sequence_check.py"), str(SKILL)],
        ),
        CheckSpec(
            "deep-skill-health",
            [
                py,
                str(SKILL_SCRIPT / "zero_to_hero_check.py"),
                str(SKILL),
                "--deep",
                "--max-seconds",
                "240",
                "--summary",
            ],
        ),
        CheckSpec(
            "pack-validation",
            [py, str(SKILL_SCRIPT / "validate_zero_to_hero_pack.py"), str(SKILL)],
        ),
        CheckSpec(
            "profile-fixture-matrix",
            [py, str(SKILL_SCRIPT / "run_fixture_tests.py"), str(SKILL)],
        ),
        CheckSpec(
            "generation-transactions",
            [py, str(SKILL_SCRIPT / "test_generation_transactions.py")],
        ),
        CheckSpec(
            "profile-generation-matrix",
            [py, str(SKILL_SCRIPT / "test_profile_generation_matrix.py")],
            timeout=300,
        ),
        CheckSpec(
            "text-to-cad-contract",
            [py, str(SKILL_SCRIPT / "test_text_to_cad_probe.py"), "--json"],
        ),
        CheckSpec(
            "eval-runner-semantics",
            [py, "tests/smoke/run_skill_eval_runner_smoke.py"],
        ),
        CheckSpec(
            "standalone-skill-archive",
            [py, "tests/smoke/run_standalone_skill_archive_smoke.py"],
        ),
        CheckSpec(
            "release-workflow-smoke",
            [py, "tests/smoke/run_release_workflow_smoke.py"],
        ),
        CheckSpec(
            "release-metadata",
            [py, "scripts/release_skill_workflow.py", "validate-metadata"],
        ),
        CheckSpec("plugin-metadata", [py, "scripts/plugin_metadata_check.py"]),
        CheckSpec("source-mirror-parity", [py, "tests/check_skill_mirror.py"]),
        CheckSpec(
            "plugin-archive-determinism",
            [py, "tests/smoke/run_plugin_archive_smoke.py", "--repeat", "2"],
            timeout=180,
        ),
        CheckSpec(
            "omx-0.20.3-integration",
            [py, str(SKILL_SCRIPT / "test_omx_integration.py"), "--json"],
            kind="external",
            status_mode="external-json",
            timeout=180,
        ),
        CheckSpec(
            "codex-skill-behavior-eval",
            [
                py,
                str(SKILL_SCRIPT / "run_skill_evals.py"),
                str(SKILL),
                "--no-model-grader",
            ],
            kind="external",
            status_mode="external-json",
            timeout=900,
        ),
        CheckSpec(
            "codex-handoff-model-grader",
            [
                py,
                str(SKILL_SCRIPT / "run_skill_evals.py"),
                str(SKILL),
                "--case",
                "explicit-web-api-handoff",
            ],
            kind="external",
            status_mode="external-json",
            timeout=420,
        ),
    ]


def parse_external_status(stdout: str) -> tuple[str, str]:
    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        return "failed", f"external check did not emit one JSON result: {exc}"
    raw = str(payload.get("status", "")).upper()
    detail = str(payload.get("message") or payload.get("reason") or "")
    if raw == "PASS":
        return "passed", detail
    if raw == "SKIP":
        return "skipped", detail
    if raw == "FAIL":
        return "failed", detail
    return "failed", f"external check emitted unsupported status {raw or '<missing>'!r}"


def run_check(spec: CheckSpec, default_timeout: int) -> CheckResult:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    start = time.monotonic()
    timeout = spec.timeout or default_timeout
    try:
        completed = subprocess.run(
            spec.command,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            name=spec.name,
            kind=spec.kind,
            status="timeout",
            seconds=round(time.monotonic() - start, 3),
            command=spec.command,
            detail=f"timed out after {timeout} seconds",
            stdout=(exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
        )

    if completed.returncode != 0:
        status = "failed"
        detail = f"exit code {completed.returncode}"
    elif spec.status_mode == "external-json":
        status, detail = parse_external_status(completed.stdout)
    else:
        status = "passed"
        detail = ""
    return CheckResult(
        name=spec.name,
        kind=spec.kind,
        status=status,  # type: ignore[arg-type]
        seconds=round(time.monotonic() - start, 3),
        command=spec.command,
        detail=detail,
        stdout=completed.stdout[-4000:],
        stderr=completed.stderr[-4000:],
    )


def print_result(result: CheckResult, *, jsonl: bool) -> None:
    if jsonl:
        print(json.dumps(asdict(result), sort_keys=True))
        return
    suffix = f": {result.detail}" if result.detail else ""
    print(f"[{result.status}] {result.name} ({result.seconds}s){suffix}")
    if result.status in {"failed", "timeout"}:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="repository root; must resolve to the zero-to-hero checkout",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="compatibility alias; the authoritative gate always runs the full plan",
    )
    parser.add_argument("--timeout", type=int, default=240, help="default per-check timeout")
    parser.add_argument("--json", action="store_true", help="emit final JSON summary")
    parser.add_argument("--jsonl", action="store_true", help="emit per-check JSON lines")
    parser.add_argument("--list-checks", action="store_true", help="list checks and exit")
    args = parser.parse_args()

    target = Path(args.repo).resolve()
    if target != REPO_ROOT:
        print(
            f"validator must target {REPO_ROOT}; got {target}",
            file=sys.stderr,
        )
        return 2
    if args.timeout < 1:
        print("--timeout must be a positive integer", file=sys.stderr)
        return 2

    plan = check_plan()
    if args.list_checks:
        for spec in plan:
            print(f"{spec.name} [{spec.kind}]: {' '.join(spec.command)}")
        return 0

    clean_runtime_artifacts(REPO_ROOT)
    results: list[CheckResult] = []
    try:
        for spec in plan:
            result = run_check(spec, args.timeout)
            results.append(result)
            print_result(result, jsonl=args.jsonl)
            clean_runtime_artifacts(REPO_ROOT)
            if result.status in {"failed", "timeout"}:
                break
    finally:
        clean_runtime_artifacts(REPO_ROOT)

    complete = len(results) == len(plan)
    failed = [result for result in results if result.status in {"failed", "timeout"}]
    hermetic_skips = [
        result
        for result in results
        if result.kind == "hermetic" and result.status == "skipped"
    ]
    ok = complete and not failed and not hermetic_skips
    summary = {
        "status": "passed" if ok else "failed",
        "checks_run": len(results),
        "checks_expected": len(plan),
        "passed": sum(result.status == "passed" for result in results),
        "skipped_external": [
            result.name
            for result in results
            if result.kind == "external" and result.status == "skipped"
        ],
        "failed": [result.name for result in failed],
        "results": [asdict(result) for result in results],
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif not args.jsonl:
        print(
            json.dumps(
                {
                    "status": summary["status"],
                    "checks_run": summary["checks_run"],
                    "checks_expected": summary["checks_expected"],
                    "passed": summary["passed"],
                    "skipped_external": summary["skipped_external"],
                    "failed": summary["failed"],
                },
                indent=2,
            )
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
