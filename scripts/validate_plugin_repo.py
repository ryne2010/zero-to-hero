#!/usr/bin/env python3
"""Bounded structural validation for the zero-to-hero plugin repository.

This runner intentionally separates deterministic repository validation from
runtime/smoke checks. Use `make smoke` for smoke behavior and `make
archive-smoke` for release archive checks.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "zero-to-hero"


@dataclass
class CheckResult:
    name: str
    status: str
    seconds: float
    command: list[str]
    stdout: str = ""
    stderr: str = ""


def clean_runtime_artifacts(root: Path) -> None:
    for path in [root / "skills", root / "plugins", root / "scripts", root / "tests"]:
        if not path.exists():
            continue
        for cache in path.rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)
        for compiled in list(path.rglob("*.pyc")) + list(path.rglob("*.pyo")):
            compiled.unlink(missing_ok=True)


def run_check(name: str, command: list[str], timeout: int, jsonl: bool) -> CheckResult:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        status = "passed" if completed.returncode == 0 else "failed"
        result = CheckResult(
            name=name,
            status=status,
            seconds=round(time.monotonic() - start, 3),
            command=command,
            stdout=completed.stdout[-4000:],
            stderr=completed.stderr[-4000:],
        )
    except subprocess.TimeoutExpired as exc:
        result = CheckResult(
            name=name,
            status="timeout",
            seconds=round(time.monotonic() - start, 3),
            command=command,
            stdout=(exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
        )
    if jsonl:
        print(json.dumps(asdict(result), sort_keys=True))
    else:
        print(f"[{result.status}] {name} ({result.seconds}s)")
        if result.status != "passed":
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
    return result


def python_files() -> list[str]:
    paths: list[Path] = []
    for base in [SKILL / "scripts", REPO_ROOT / "scripts", REPO_ROOT / "tests"]:
        if base.exists():
            paths.extend(sorted(base.rglob("*.py")))
    return [str(path.relative_to(REPO_ROOT)) for path in paths]


def check_plan(deep: bool) -> list[tuple[str, list[str]]]:
    py_compile_cmd = [sys.executable, "-m", "py_compile", *python_files()]
    checks: list[tuple[str, list[str]]] = [
        ("python-compile", py_compile_cmd),
        ("mirror-parity", [sys.executable, "tests/check_skill_mirror.py"]),
        ("skill-health", [sys.executable, str(SKILL / "scripts" / "zero_to_hero_check.py"), str(SKILL), "--deep", "--max-seconds", "240", "--summary"]),
        ("release-metadata", [sys.executable, "scripts/release_skill_workflow.py", "validate-metadata"]),
        ("plugin-metadata", [sys.executable, "scripts/plugin_metadata_check.py"]),
    ]
    if deep:
        checks.extend([
            ("yaml-parse", [sys.executable, str(SKILL / "scripts" / "yaml_parse_check.py"), str(SKILL)]),
            ("docs-reference", [sys.executable, str(SKILL / "scripts" / "docs_reference_check.py"), str(SKILL)]),
            ("prompt-sequence", [sys.executable, str(SKILL / "scripts" / "prompt_sequence_check.py"), str(SKILL)]),
            ("canonical-cleanup", [sys.executable, str(SKILL / "scripts" / "canonical_cleanup_check.py"), str(SKILL)]),
        ])
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Repository root; defaults to current directory.")
    parser.add_argument("--deep", action="store_true", help="Run deeper deterministic structural checks.")
    parser.add_argument("--timeout", type=int, default=90, help="Per-check timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit final JSON summary.")
    parser.add_argument("--jsonl", action="store_true", help="Emit per-check JSON lines.")
    parser.add_argument("--list-checks", action="store_true", help="List checks and exit.")
    args = parser.parse_args()

    target = Path(args.repo).resolve()
    if target != REPO_ROOT:
        print(f"validate_plugin_repo.py must run from this repo root; got {target}, expected {REPO_ROOT}", file=sys.stderr)
        return 2

    plan = check_plan(args.deep)
    if args.list_checks:
        for name, command in plan:
            print(f"{name}: {' '.join(command)}")
        return 0

    clean_runtime_artifacts(REPO_ROOT)
    results: list[CheckResult] = []
    for name, command in plan:
        result = run_check(name, command, args.timeout, args.jsonl)
        results.append(result)
        clean_runtime_artifacts(REPO_ROOT)
        if result.status != "passed":
            break
    clean_runtime_artifacts(REPO_ROOT)

    ok = all(result.status == "passed" for result in results) and len(results) == len(plan)
    summary = {
        "status": "passed" if ok else "failed",
        "deep": args.deep,
        "checks_run": len(results),
        "checks_expected": len(plan),
        "results": [asdict(result) for result in results],
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif not args.jsonl:
        print(json.dumps({"status": summary["status"], "checks_run": summary["checks_run"], "checks_expected": summary["checks_expected"]}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
