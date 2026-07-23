#!/usr/bin/env python3
"""Exercise external eval runner PASS, SKIP, and FAIL status semantics."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "zero-to-hero"
RUNNER = SKILL / "scripts" / "run_skill_evals.py"

FAKE_CODEX = """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

args = sys.argv[1:]
if args == ["--version"]:
    print("codex-fake 1.0")
    raise SystemExit(0)
if args == ["exec", "--help"]:
    print("--json --sandbox --cd --skip-git-repo-check --ephemeral "
          "--ignore-user-config --ask-for-approval --output-schema --output-last-message")
    raise SystemExit(0)
if not args or args[0] != "exec":
    raise SystemExit(2)
workspace = Path(args[args.index("--cd") + 1])
if not (workspace / ".agents/skills/zero-to-hero/SKILL.md").is_file():
    print("repo-scoped skill was not installed", file=sys.stderr)
    raise SystemExit(3)
if "--output-schema" in args:
    schema = Path(args[args.index("--output-schema") + 1])
    expected_schema = (
        workspace
        / ".agents/skills/zero-to-hero/evals/handoff-quality-rubric.schema.json"
    )
    if schema != expected_schema or not schema.is_file():
        print("grader schema is not the isolated skill copy", file=sys.stderr)
        raise SystemExit(4)
    output = Path(args[args.index("-o") + 1])
    rubric_ids = [
        "target_specificity",
        "commands_and_harness",
        "phase_and_ownership",
        "profile_artifacts",
        "evidence_and_done",
        "safety_boundaries",
        "unresolved_risks",
    ]
    output.write_text(json.dumps({
        "overall_pass": True,
        "score": 100,
        "checks": [
            {
                "id": check_id,
                "pass": True,
                "score": 4,
                "notes": "verified",
                "evidence": ["README.md"],
            }
            for check_id in rubric_ids
        ],
        "summary": "verified",
    }))
    print(json.dumps({
        "type": "item.completed",
        "item": {
            "id": "grader_0",
            "type": "agent_message",
            "text": "structured grade written"
        }
    }))
    raise SystemExit(0)
prompt = args[-1]
if "UNAVAILABLE_CASE" in prompt:
    print("not logged in", file=sys.stderr)
    raise SystemExit(1)
command = "pwd"
if "SKILL_INVOKED_CASE" in prompt:
    command = "sed -n '1,240p' .agents/skills/zero-to-hero/SKILL.md"
elif "SKILL_INVOKED_WINDOWS_CASE" in prompt:
    command = r"type .agents\\skills\\zero-to-hero\\SKILL.md"
elif "SKILL_SPOOF_CASE" in prompt:
    command = "echo .agents/skills/zero-to-hero/SKILL.md"
for event_type in ("item.started", "item.completed"):
    print(json.dumps({
        "type": event_type,
        "item": {
            "id": "command_0",
            "type": "command_execution",
            "command": command
        }
    }))
print(json.dumps({
    "type": "item.completed",
    "item": {
        "id": "item_0",
        "type": "agent_message",
        "text": "ordinary bounded response"
    }
}))
"""


def write_python_command(root: Path, name: str, source: str) -> Path:
    """Create a directly invokable Python-backed command on POSIX and Windows."""

    script = root / f"{name}.py"
    script.write_text(source, encoding="utf-8")
    if os.name == "nt":
        command = root / f"{name}.cmd"
        command.write_text(
            f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n',
            encoding="utf-8",
        )
    else:
        command = root / name
        command.write_text(source, encoding="utf-8")
        command.chmod(0o755)
    return command


def suite(
    *,
    prompt: str,
    should_invoke: bool = False,
    expected_path: str | None = None,
    model_grader: bool = False,
    case_id: str = "status-case",
):
    expected_paths = ["**/README.md"]
    if expected_path:
        expected_paths.append(expected_path)
    checks: dict[str, object] = {
        "require_unchanged_workspace": True,
        "expected_all_paths": expected_paths,
        "max_command_count": 1,
    }
    return {
        "schema": "zero-to-hero.skill-evals.v1",
        "defaults": {
            "timeout_seconds": 10,
            "max_command_count": 5,
            "model_grader_minimum_score": 80,
        },
        "cases": [
            {
                "id": case_id,
                "category": "runner_status",
                "should_invoke": should_invoke,
                "sandbox": "read-only",
                "prompt": prompt,
                "setup_files": {"README.md": "# Fixture\n"},
                "checks": checks,
                "model_grader": model_grader,
            }
        ],
    }


def run(
    fake_codex: Path,
    cases_path: Path,
    *extra: str,
) -> tuple[int, dict[str, object], str]:
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            str(SKILL),
            "--codex",
            str(fake_codex),
            "--cases",
            str(cases_path),
            *extra,
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"eval runner emitted invalid JSON: {exc}\n{result.stdout}\n{result.stderr}"
        ) from exc
    return result.returncode, payload, result.stderr


def assert_result(
    actual: tuple[int, dict[str, object], str],
    *,
    returncode: int,
    status: str,
) -> None:
    actual_returncode, payload, stderr = actual
    if actual_returncode != returncode or payload.get("status") != status:
        raise SystemExit(
            "unexpected eval runner result: "
            f"returncode={actual_returncode}, payload={payload}, stderr={stderr}"
        )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="zero-to-hero-eval-runner-smoke-") as temp:
        root = Path(temp)
        fake_codex = write_python_command(root, "codex-fake", FAKE_CODEX)
        cases_path = root / "cases.json"

        cases_path.write_text(json.dumps(suite(prompt="PASS_CASE")), encoding="utf-8")
        assert_result(run(fake_codex, cases_path), returncode=0, status="PASS")

        cases_path.write_text(
            json.dumps(suite(prompt="PASS_CASE", case_id="../../escaped")),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=1, status="FAIL")

        cases_path.write_text(
            json.dumps(suite(prompt="PASS_CASE", should_invoke=True)),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=1, status="FAIL")

        cases_path.write_text(
            json.dumps(
                suite(prompt="SKILL_INVOKED_CASE", should_invoke=True)
            ),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=0, status="PASS")

        cases_path.write_text(
            json.dumps(
                suite(prompt="SKILL_INVOKED_WINDOWS_CASE", should_invoke=True)
            ),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=0, status="PASS")

        cases_path.write_text(
            json.dumps(
                suite(prompt="SKILL_SPOOF_CASE", should_invoke=True)
            ),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=1, status="FAIL")

        cases_path.write_text(
            json.dumps(suite(prompt="SKILL_INVOKED_CASE")),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=1, status="FAIL")

        cases_path.write_text(
            json.dumps(suite(prompt="FAIL_CASE", expected_path="missing.file")),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=1, status="FAIL")

        cases_path.write_text(
            json.dumps(suite(prompt="UNAVAILABLE_CASE")),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=0, status="SKIP")
        assert_result(
            run(fake_codex, cases_path, "--require-codex"),
            returncode=2,
            status="SKIP",
        )

        cases_path.write_text(
            json.dumps(suite(prompt="MODEL_CASE", model_grader=True)),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=0, status="PASS")
        assert_result(
            run(fake_codex, cases_path, "--no-model-grader"),
            returncode=0,
            status="PASS",
        )

        cases_path.write_text(
            json.dumps(suite(prompt="network diagram compiler failure")),
            encoding="utf-8",
        )
        fake_source = FAKE_CODEX.replace(
            'if "UNAVAILABLE_CASE" in prompt:',
            'if "network diagram compiler failure" in prompt:\n'
            '    print(json.dumps({"type": "item.completed", "item": '
            '{"id": "message_0", "type": "agent_message", '
            '"text": "network diagram"}}))\n'
            '    print("compiler failed", file=sys.stderr)\n'
            '    raise SystemExit(1)\n'
            'if "UNAVAILABLE_CASE" in prompt:',
        )
        failing_codex = write_python_command(root, "codex-failure", fake_source)
        assert_result(
            run(failing_codex, cases_path),
            returncode=1,
            status="FAIL",
        )

    print("skill eval runner smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
