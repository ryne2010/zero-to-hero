#!/usr/bin/env python3
"""Run bounded smoke checks for the zero-to-hero plugin repo."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class SmokeResult:
    name: str
    status: str
    seconds: float
    command: list[str]
    stdout: str = ""
    stderr: str = ""


def run(name: str, command: list[str], timeout: int, jsonl: bool) -> SmokeResult:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    start = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=timeout)
        status = "passed" if completed.returncode == 0 else "failed"
        result = SmokeResult(name, status, round(time.monotonic() - start, 3), command, completed.stdout[-4000:], completed.stderr[-4000:])
    except subprocess.TimeoutExpired as exc:
        result = SmokeResult(name, "timeout", round(time.monotonic() - start, 3), command, (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "", (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=120, help="Per-smoke timeout in seconds.")
    parser.add_argument("--jsonl", action="store_true")
    args = parser.parse_args()
    checks = [
        ("skill-smoke", [sys.executable, "tests/smoke/run_skill_smoke.py"]),
        ("release-workflow-smoke", [sys.executable, "tests/smoke/run_release_workflow_smoke.py"]),
    ]
    results = []
    for name, command in checks:
        result = run(name, command, args.timeout, args.jsonl)
        results.append(result)
        if result.status != "passed":
            break
    ok = all(result.status == "passed" for result in results) and len(results) == len(checks)
    if not args.jsonl:
        print(json.dumps({"status": "passed" if ok else "failed", "checks_run": len(results), "checks_expected": len(checks)}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
