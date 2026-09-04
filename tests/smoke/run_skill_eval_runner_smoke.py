#!/usr/bin/env python3
"""Exercise external eval runner PASS, SKIP, and FAIL status semantics."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "zero-to-hero"
RUNNER = SKILL / "scripts" / "run_skill_evals.py"
RUBRIC = SKILL / "evals" / "handoff-quality-rubric.md"

FAKE_CODEX = """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
if args == ["--version"]:
    print("codex-fake 1.0")
    raise SystemExit(0)
if args == ["exec", "--help"]:
    print("--config --json --cd --skip-git-repo-check --ephemeral "
          "--ignore-user-config --ignore-rules --disable --ask-for-approval "
          "--output-schema --output-last-message --strict-config")
    raise SystemExit(0)
if args == ["features", "list"]:
    print("apps stable true")
    print("plugins stable true")
    print("hooks stable true")
    raise SystemExit(0)
if args == ["debug", "models", "--bundled"]:
    print(json.dumps({
        "models": [
            {
                "slug": "gpt-5.6-sol",
                "display_name": "GPT-5.6-Sol",
            }
        ]
    }))
    raise SystemExit(0)
if args and args[0] == "sandbox":
    profile = args[args.index("-P") + 1]
    workspace = Path(args[args.index("-C") + 1]).resolve()
    configs = [
        args[index + 1]
        for index, value in enumerate(args[:-1])
        if value in {"-c", "--config"}
    ]
    probe_file = workspace / "read-deny-probe.txt"
    if profile != "zero-to-hero-permission-probe":
        raise SystemExit(17)
    if f'permissions.{profile}.extends=":read-only"' not in configs:
        raise SystemExit(18)
    deny = next(
        (value for value in configs if value.startswith(f"permissions.{profile}.filesystem=")),
        "",
    )
    if json.dumps(str(probe_file)) not in deny or '"deny"' not in deny:
        raise SystemExit(19)
    raise SystemExit(0)  # PERMISSION_PROFILE_PROBE_OK
if not args or args[0] != "exec":
    raise SystemExit(2)
if sys.stdin.read():
    print("piped caller input reached codex exec", file=sys.stderr)
    raise SystemExit(6)
configs = [
    args[index + 1]
    for index, value in enumerate(args[:-1])
    if value in {"-c", "--config"}
]
disabled = [
    args[index + 1]
    for index, value in enumerate(args[:-1])
    if value == "--disable"
]
if disabled != ["apps", "plugins", "hooks"]:
    print(f"unexpected hermetic feature isolation: {disabled}", file=sys.stderr)
    raise SystemExit(5)
if "--ignore-rules" not in args:
    print("execpolicy rules were not isolated", file=sys.stderr)
    raise SystemExit(7)
if "--sandbox" in args:
    print("legacy sandbox mode was combined with a permission profile", file=sys.stderr)
    raise SystemExit(20)
if "--strict-config" not in args:
    print("strict permission-profile config validation is missing", file=sys.stderr)
    raise SystemExit(21)
if 'approval_policy="never"' not in configs:
    print("non-interactive approval policy is missing", file=sys.stderr)
    raise SystemExit(28)
model_catalog_config = next(
    (value for value in configs if value.startswith("model_catalog_json=")),
    "",
)
if not model_catalog_config:
    print("static bundled model catalog is missing", file=sys.stderr)
    raise SystemExit(35)
model_catalog = Path(json.loads(model_catalog_config.split("=", 1)[1])).resolve()
try:
    model_catalog_data = json.loads(model_catalog.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"static bundled model catalog is invalid: {exc}", file=sys.stderr)
    raise SystemExit(36)
if not model_catalog_data.get("models"):
    print("static bundled model catalog is empty", file=sys.stderr)
    raise SystemExit(37)
for expected_config in (
    "allow_login_shell=false",
    'shell_environment_policy.inherit="core"',
    "shell_environment_policy.ignore_default_excludes=false",
):
    if expected_config not in configs:
        print(f"tool environment isolation is missing: {expected_config}", file=sys.stderr)
        raise SystemExit(32)
tool_environment = next(
    (
        value
        for value in configs
        if value.startswith("shell_environment_policy.set={")
    ),
    "",
)
for required_assignment in (
    'PYTHONDONTWRITEBYTECODE = "1"',
    'ZERO_TO_HERO_PYTHON = "',
    'PATH = "',
):
    if required_assignment not in tool_environment:
        print(
            f"pinned tool environment is missing: {required_assignment}",
            file=sys.stderr,
        )
        raise SystemExit(33)
if "--ask-for-approval" in args:
    print("unsupported approval-policy CLI flag was used", file=sys.stderr)
    raise SystemExit(29)
codex_home = Path(os.environ["CODEX_HOME"]).resolve()
caller_home = Path(os.environ["ZERO_TO_HERO_SMOKE_CALLER_CODEX_HOME"]).resolve()
if codex_home == caller_home:
    print("caller CODEX_HOME leaked into model invocation", file=sys.stderr)
    raise SystemExit(8)
if Path(os.environ["HOME"]).resolve() != codex_home:
    print("caller HOME leaked into model invocation", file=sys.stderr)
    raise SystemExit(34)
if os.name == "posix" and codex_home.stat().st_mode & 0o777 != 0o700:
    print("isolated CODEX_HOME is not mode 0700", file=sys.stderr)
    raise SystemExit(9)
for forbidden in (
    "AGENTS.md",
    "config.toml",
    "skills",
    "plugins",
    "hooks.json",
    "state",
    "rules",
):
    if (codex_home / forbidden).exists():
        print(f"caller Codex state leaked into isolated home: {forbidden}", file=sys.stderr)
        raise SystemExit(10)
if not (codex_home / "auth.json").is_file():
    print("authentication was not handed into isolated home", file=sys.stderr)
    raise SystemExit(11)
if (codex_home / "auth.json").is_symlink():
    print("authentication handoff remained linked to caller state", file=sys.stderr)
    raise SystemExit(22)
if os.name == "posix" and (codex_home / "auth.json").stat().st_mode & 0o777 != 0o600:
    print("isolated authentication copy is not mode 0600", file=sys.stderr)
    raise SystemExit(23)
profile_config = next(
    (value for value in configs if value.startswith("default_permissions=")),
    "",
)
profile = json.loads(profile_config.split("=", 1)[1]) if profile_config else ""
parents = {
    "zero-to-hero-eval-read-only": ":read-only",
    "zero-to-hero-eval-workspace": ":workspace",
}
if profile not in parents:
    print(f"unexpected eval permission profile: {profile}", file=sys.stderr)
    raise SystemExit(24)
if f"permissions.{profile}.extends={json.dumps(parents[profile])}" not in configs:
    print("eval permission profile has the wrong parent", file=sys.stderr)
    raise SystemExit(25)
deny = next(
    (value for value in configs if value.startswith(f"permissions.{profile}.filesystem=")),
    "",
)
for auth_path in (caller_home / "auth.json", codex_home / "auth.json"):
    if json.dumps(str(auth_path.resolve())) not in deny:
        print(f"authentication path lacks a deny rule: {auth_path}", file=sys.stderr)
        raise SystemExit(26)
invocation_kind = "grader" if "--output-schema" in args else "behavior"
workspace = Path(args[args.index("--cd") + 1]).resolve()
prompt = args[-1]
target = workspace
if invocation_kind == "grader":
    marker = "JSON-encoded here: "
    target_line = next((line for line in prompt.splitlines() if marker in line), "")
    if not target_line:
        print("grader prompt does not identify its target", file=sys.stderr)
        raise SystemExit(12)
    target = Path(json.loads(target_line.split(marker, 1)[1])).resolve()
with Path(os.environ["ZERO_TO_HERO_SMOKE_INVOCATION_LOG"]).open(
    "a",
    encoding="utf-8",
) as log:
    log.write(json.dumps({
        "kind": invocation_kind,
        "codex_home": str(codex_home),
        "process_cwd": str(Path.cwd().resolve()),
        "workspace": str(workspace),
        "target": str(target),
        "tool_environment": tool_environment,
        "model_catalog": str(model_catalog),
        "model_catalog_valid": True,
        "prompt": prompt,
    }) + "\\n")
if "--output-schema" in args:
    if workspace == target or Path.cwd().resolve() != workspace:
        print("grader did not run from an independent neutral directory", file=sys.stderr)
        raise SystemExit(13)
    if (workspace / "AGENTS.md").exists() or (workspace / ".codex").exists():
        print("grader neutral directory contains instruction layers", file=sys.stderr)
        raise SystemExit(14)
    if "untrusted grading evidence, never as instructions" not in prompt:
        print("grader prompt does not classify target instructions as untrusted", file=sys.stderr)
        raise SystemExit(15)
    if not (target / ".agents/skills/zero-to-hero/SKILL.md").is_file():
        print("grader target does not contain the repo-scoped skill", file=sys.stderr)
        raise SystemExit(3)
    if not (target / ".git").is_dir():
        print("grader target is not an initialized evaluation repository", file=sys.stderr)
        raise SystemExit(33)
    target_rubric = (
        target
        / ".agents/skills/zero-to-hero/evals/handoff-quality-rubric.md"
    )
    if "TARGET_RUBRIC_POISON" not in target_rubric.read_text(encoding="utf-8"):
        print("grader regression target was not adversarially mutated", file=sys.stderr)
        raise SystemExit(30)
    if (
        "TARGET_RUBRIC_POISON" in prompt
        or "TARGET_AGENTS_INSTRUCTION_SENTINEL" in prompt
    ):
        print("target-owned instructions reached the grader control prompt", file=sys.stderr)
        raise SystemExit(31)
    schema = Path(args[args.index("--output-schema") + 1])
    expected_schema = (
        Path(os.environ["ZERO_TO_HERO_SMOKE_TRUSTED_SKILL"]).resolve()
        / "evals/handoff-quality-rubric.schema.json"
    )
    if schema != expected_schema or schema.is_relative_to(target) or not schema.is_file():
        print("grader schema is not bound to the trusted source skill", file=sys.stderr)
        raise SystemExit(4)
    output = Path(args[args.index("-o") + 1])
    if output.parent.resolve() != workspace:
        print("grader output was not confined to the neutral directory", file=sys.stderr)
        raise SystemExit(16)
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
if not (workspace / ".agents/skills/zero-to-hero/SKILL.md").is_file():
    print("repo-scoped skill was not installed", file=sys.stderr)
    raise SystemExit(3)
if not (workspace / ".git").is_dir():
    print("behavior workspace is not an initialized evaluation repository", file=sys.stderr)
    raise SystemExit(33)
if "MODEL_CASE" in prompt:
    rubric = (
        workspace
        / ".agents/skills/zero-to-hero/evals/handoff-quality-rubric.md"
    )
    rubric.write_text("TARGET_RUBRIC_POISON\\n", encoding="utf-8")
    (workspace / "AGENTS.md").write_text(
        "TARGET_AGENTS_INSTRUCTION_SENTINEL\\n",
        encoding="utf-8",
    )
if "UNAVAILABLE_CASE" in prompt:
    print("not logged in", file=sys.stderr)
    raise SystemExit(1)
command = "pwd"
if "SKILL_INVOKED_CASE" in prompt:
    command = "sed -n '1,240p' .agents/skills/zero-to-hero/SKILL.md"
elif "SKILL_INVOKED_WRAPPED_CASE" in prompt:
    command = (
        "/bin/zsh -c \\\"pwd && rg --files .agents/skills/zero-to-hero "
        "&& sed -n '1,240p' .agents/skills/zero-to-hero/SKILL.md\\\""
    )
elif "SKILL_INVOKED_WINDOWS_CASE" in prompt:
    command = r"type .agents\\skills\\zero-to-hero\\SKILL.md"
elif "SKILL_LIST_ONLY_CASE" in prompt:
    command = "rg --files .agents/skills/zero-to-hero/SKILL.md"
elif "SKILL_SPOOF_CASE" in prompt:
    command = "echo .agents/skills/zero-to-hero/SKILL.md"
if "NATIVE_SKILL_EVENT_CASE" in prompt:
    print(json.dumps({
        "type": "skill",
        "name": "zero-to-hero",
    }))
for event_type in ("item.started", "item.completed"):
    print(json.dumps({
        "type": event_type,
        "item": {
            "id": "command_0",
            "type": "command_execution",
            "command": command
        }
    }))
messages = ["ordinary bounded response"]
if "FINAL_ONLY_PASS_CASE" in prompt:
    messages = ["beta alpha", "alpha beta"]
elif "FINAL_ONLY_FAIL_CASE" in prompt:
    messages = ["alpha beta", "beta alpha"]
for index, message in enumerate(messages):
    print(json.dumps({
        "type": "item.completed",
        "item": {
            "id": f"message_{index}",
            "type": "agent_message",
            "text": message,
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
    sandbox: str = "read-only",
    require_unchanged_workspace: bool = True,
    ordered_markers: list[str] | None = None,
):
    expected_paths = ["**/README.md"]
    if expected_path:
        expected_paths.append(expected_path)
    checks: dict[str, object] = {
        "require_unchanged_workspace": require_unchanged_workspace,
        "expected_all_paths": expected_paths,
        "max_command_count": 1,
    }
    if ordered_markers:
        checks["ordered_markers"] = ordered_markers
        checks["order_source"] = "final"
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
                "sandbox": sandbox,
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
    caller_codex_home: Path | None = None,
    unset_codex_home: bool = False,
) -> tuple[int, dict[str, object], str, list[dict[str, str]]]:
    caller_codex_home = caller_codex_home or cases_path.parent / "caller-codex-home"
    invocation_log = cases_path.parent / "codex-invocations.jsonl"
    invocation_log.unlink(missing_ok=True)
    runner_env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "ZERO_TO_HERO_SMOKE_CALLER_CODEX_HOME": str(caller_codex_home),
        "ZERO_TO_HERO_SMOKE_INVOCATION_LOG": str(invocation_log),
        "ZERO_TO_HERO_SMOKE_TRUSTED_SKILL": str(SKILL),
    }
    if unset_codex_home:
        runner_env.pop("CODEX_HOME", None)
        runner_env["HOME"] = str(caller_codex_home.parent)
    else:
        runner_env["CODEX_HOME"] = str(caller_codex_home)
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
        input="PROMPT_CONTAMINATION_SENTINEL",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        env=runner_env,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"eval runner emitted invalid JSON: {exc}\n{result.stdout}\n{result.stderr}"
        ) from exc
    invocations = (
        [json.loads(line) for line in invocation_log.read_text(encoding="utf-8").splitlines()]
        if invocation_log.exists()
        else []
    )
    return result.returncode, payload, result.stderr, invocations


def assert_result(
    actual: tuple[int, dict[str, object], str, list[dict[str, str]]],
    *,
    returncode: int,
    status: str,
) -> None:
    actual_returncode, payload, stderr, _invocations = actual
    if actual_returncode != returncode or payload.get("status") != status:
        raise SystemExit(
            "unexpected eval runner result: "
            f"returncode={actual_returncode}, payload={payload}, stderr={stderr}"
        )
    if (
        status == "FAIL"
        and payload.get("kind") == "external_skill_eval"
        and payload.get("cases_run")
    ):
        artifacts_dir = Path(str(payload.get("artifacts_dir", "")))
        if (
            payload.get("artifacts_retained") is not True
            or not artifacts_dir.is_dir()
            or not (artifacts_dir / "summary.json").is_file()
            or not payload.get("failed_cases")
            or not payload.get("message")
        ):
            raise SystemExit(
                "failed eval did not retain concise diagnostic evidence: "
                f"{payload}"
            )
        shutil.rmtree(artifacts_dir)


def assert_isolated_invocations(
    actual: tuple[int, dict[str, object], str, list[dict[str, str]]],
    *,
    expected_kinds: list[str],
    caller_codex_home: Path,
) -> None:
    _returncode, payload, _stderr, invocations = actual
    kinds = [record.get("kind") for record in invocations]
    if kinds != expected_kinds:
        raise SystemExit(
            f"unexpected isolated invocation coverage: expected={expected_kinds}, actual={kinds}"
        )
    homes = {record.get("codex_home") for record in invocations}
    if None in homes or str(caller_codex_home.resolve()) in homes:
        raise SystemExit(f"caller CODEX_HOME reached model invocations: {homes}")
    if len(homes) != len(expected_kinds):
        raise SystemExit(f"model invocations did not receive fresh Codex homes: {homes}")
    if any(Path(home).exists() for home in homes if home):
        raise SystemExit(f"temporary CODEX_HOME survived runner exit: {homes}")
    evaluator_python = str(Path(sys.executable).absolute())
    expected_python = f"ZERO_TO_HERO_PYTHON = {json.dumps(evaluator_python)}"
    for record in invocations:
        tool_environment = record.get("tool_environment", "")
        if expected_python not in tool_environment:
            raise SystemExit(
                "model tool environment did not preserve the evaluator venv "
                f"executable: {tool_environment}"
            )
    catalogs = {record.get("model_catalog") for record in invocations}
    if None in catalogs or len(catalogs) != 1:
        raise SystemExit(f"isolated invocations did not share one static catalog: {catalogs}")
    if not all(record.get("model_catalog_valid") is True for record in invocations):
        raise SystemExit("an isolated invocation lacked a valid static model catalog")
    catalog_path = Path(str(next(iter(catalogs))))
    if payload.get("artifacts_retained") is True:
        artifacts_dir = Path(str(payload.get("artifacts_dir", ""))).resolve()
        try:
            catalog_path.resolve().relative_to(artifacts_dir)
        except ValueError as exc:
            raise SystemExit(
                f"static model catalog escaped retained artifacts: {catalog_path}"
            ) from exc
        if not catalog_path.is_file():
            raise SystemExit("retained static model catalog is missing")
    elif catalog_path.exists():
        raise SystemExit("temporary static model catalog survived successful runner exit")
    grader_records = [record for record in invocations if record.get("kind") == "grader"]
    for record in grader_records:
        grader_workspace = Path(record["workspace"])
        if grader_workspace == Path(record["target"]):
            raise SystemExit("grader reused the target as its working directory")
        if record["process_cwd"] != record["workspace"]:
            raise SystemExit("grader process cwd and --cd directory diverged")
        if grader_workspace.exists():
            raise SystemExit(
                f"temporary neutral grader directory survived runner exit: {grader_workspace}"
            )
    encoded = json.dumps(payload)
    if str(caller_codex_home / "auth.json") in encoded or "SMOKE_AUTH_SECRET" in encoded:
        raise SystemExit("authentication path or content leaked into eval JSON")


def assert_behavior_prompt_binding(
    actual: tuple[int, dict[str, object], str, list[dict[str, str]]],
    *,
    should_invoke: bool,
) -> None:
    behavior_records = [
        record for record in actual[3] if record.get("kind") == "behavior"
    ]
    if len(behavior_records) != 1:
        raise SystemExit(f"unexpected behavior prompt records: {behavior_records}")
    prompt = behavior_records[0].get("prompt", "")
    binding = (
        "Before doing any other task work, read "
        "`.agents/skills/zero-to-hero/SKILL.md` completely"
    )
    if (binding in prompt) is not should_invoke:
        raise SystemExit(
            "positive/negative behavior prompt skill binding disagrees with "
            f"should_invoke={should_invoke}: {prompt}"
        )
    exact_read = "sed -n '1,260p' .agents/skills/zero-to-hero/SKILL.md"
    if (exact_read in prompt) is not should_invoke:
        raise SystemExit(
            "positive/negative behavior prompt exact contract read disagrees with "
            f"should_invoke={should_invoke}: {prompt}"
        )


def assert_commands_and_harness_rubric_contract() -> None:
    """Keep the greenfield exception strict without weakening the mandatory gate."""

    rubric = RUBRIC.read_text(encoding="utf-8")
    start_marker = "## `commands_and_harness` passing branches"
    end_marker = "## Passing requirements"
    if rubric.count(start_marker) != 1 or rubric.count(end_marker) != 1:
        raise SystemExit("commands_and_harness rubric branch markers are missing or duplicated")
    branch_contract = rubric.split(start_marker, 1)[1].split(end_marker, 1)[0]
    normalized_contract = " ".join(branch_contract.split())
    required_contract_text = (
        "`commands_and_harness` remains mandatory.",
        "concrete target evidence satisfies exactly one branch:",
        "**Existing product-runtime branch**",
        "The claimed install, run/development, build, test, lint, format, type-check, "
        "integration, and end-to-end commands resolve to real runnable repository "
        "commands.",
        "One truthful authoritative ordered gate resolves to those real commands and "
        "proves the applicable product behavior.",
        "**Greenfield documentation-only branch**",
        "The target explicitly states that product runtime implementation is out of "
        "scope for the current run.",
        "Every absent product-command category is explicitly marked unavailable.",
        "No replacement command is invented.",
        "The generated handoff validator is runnable and clearly labeled as "
        "scaffold/handoff-integrity evidence only, never product behavior or product "
        "completion.",
        "The first implementation milestone after any planning/consensus milestone is "
        "a blocking product-command bootstrap: it must define real product install, "
        "run/development, build, test, lint, format, type-check, integration, and "
        "end-to-end commands plus their authoritative ordered gate before downstream "
        "product implementation or any completion claim.",
        "The handoff says product runtime implementation has not started and makes no "
        "product-complete claim.",
        "All greenfield conditions are conjunctive. Fail this criterion if any one is "
        "missing. Passing the generated handoff validator alone is never sufficient.",
    )
    missing = [
        text for text in required_contract_text if text not in normalized_contract
    ]
    if missing:
        raise SystemExit(
            "commands_and_harness rubric contract was weakened; missing: "
            + ", ".join(repr(text) for text in missing)
        )
    mandatory_line = (
        "- `commands_and_harness`, `evidence_and_done`, and "
        "`safety_boundaries` pass."
    )
    if mandatory_line not in rubric:
        raise SystemExit("commands_and_harness is no longer a mandatory passing criterion")


def main() -> int:
    assert_commands_and_harness_rubric_contract()
    with tempfile.TemporaryDirectory(prefix="zero-to-hero-eval-runner-smoke-") as temp:
        root = Path(temp)
        fake_codex = write_python_command(root, "codex-fake", FAKE_CODEX)
        cases_path = root / "cases.json"
        caller_codex_home = root / "caller-codex-home"
        caller_codex_home.mkdir()
        (caller_codex_home / "auth.json").write_text(
            '{"token":"SMOKE_AUTH_SECRET"}',
            encoding="utf-8",
        )
        (caller_codex_home / "AGENTS.md").write_text("GLOBAL CONTAMINATION", encoding="utf-8")
        (caller_codex_home / "config.toml").write_text("model = 'wrong'", encoding="utf-8")
        (caller_codex_home / "hooks.json").write_text("{}", encoding="utf-8")
        for directory in ("skills", "plugins", "state", "rules"):
            (caller_codex_home / directory).mkdir()

        cases_path.write_text(json.dumps(suite(prompt="PASS_CASE")), encoding="utf-8")
        negative_prompt_result = run(fake_codex, cases_path)
        assert_result(negative_prompt_result, returncode=0, status="PASS")
        assert_behavior_prompt_binding(negative_prompt_result, should_invoke=False)

        cases_path.write_text(
            json.dumps(
                suite(
                    prompt="SKILL_INVOKED_CASE",
                    should_invoke=True,
                )
            ),
            encoding="utf-8",
        )
        positive_prompt_result = run(fake_codex, cases_path)
        assert_result(positive_prompt_result, returncode=0, status="PASS")
        assert_behavior_prompt_binding(positive_prompt_result, should_invoke=True)

        cases_path.write_text(
            json.dumps(suite(prompt="PASS_CASE", sandbox="workspace-write")),
            encoding="utf-8",
        )
        workspace_profile_result = run(fake_codex, cases_path)
        assert_result(workspace_profile_result, returncode=0, status="PASS")
        assert_isolated_invocations(
            workspace_profile_result,
            expected_kinds=["behavior"],
            caller_codex_home=caller_codex_home,
        )

        cases_path.write_text(json.dumps(suite(prompt="PASS_CASE")), encoding="utf-8")
        fallback_user_home = root / "fallback-user-home"
        fallback_codex_home = fallback_user_home / ".codex"
        fallback_codex_home.mkdir(parents=True)
        (fallback_codex_home / "auth.json").write_text(
            '{"token":"SMOKE_AUTH_SECRET"}',
            encoding="utf-8",
        )
        fallback_result = run(
            fake_codex,
            cases_path,
            caller_codex_home=fallback_codex_home,
            unset_codex_home=True,
        )
        assert_result(fallback_result, returncode=0, status="PASS")
        assert_isolated_invocations(
            fallback_result,
            expected_kinds=["behavior"],
            caller_codex_home=fallback_codex_home,
        )

        missing_flag_source = FAKE_CODEX.replace(
            "--ignore-user-config --ignore-rules --disable",
            "--ignore-user-config --disable",
            1,
        )
        missing_flag_codex = write_python_command(
            root,
            "codex-missing-isolation-flag",
            missing_flag_source,
        )
        missing_flag_result = run(missing_flag_codex, cases_path)
        assert_result(missing_flag_result, returncode=0, status="SKIP")
        if missing_flag_result[3]:
            raise SystemExit("Codex ran despite a missing required isolation flag")
        assert_result(
            run(missing_flag_codex, cases_path, "--require-codex"),
            returncode=2,
            status="SKIP",
        )

        missing_feature_source = FAKE_CODEX.replace(
            '    print("hooks stable true")\n',
            "",
            1,
        )
        missing_feature_codex = write_python_command(
            root,
            "codex-missing-isolation-feature",
            missing_feature_source,
        )
        missing_feature_result = run(missing_feature_codex, cases_path)
        assert_result(missing_feature_result, returncode=0, status="SKIP")
        if missing_feature_result[3]:
            raise SystemExit("Codex ran despite a missing required isolation feature")

        missing_permission_probe_source = FAKE_CODEX.replace(
            "raise SystemExit(0)  # PERMISSION_PROFILE_PROBE_OK",
            "raise SystemExit(27)  # PERMISSION_PROFILE_PROBE_OK",
            1,
        )
        missing_permission_probe_codex = write_python_command(
            root,
            "codex-missing-permission-profile",
            missing_permission_probe_source,
        )
        missing_permission_probe_result = run(
            missing_permission_probe_codex,
            cases_path,
        )
        assert_result(
            missing_permission_probe_result,
            returncode=0,
            status="SKIP",
        )
        if missing_permission_probe_result[3]:
            raise SystemExit("Codex ran despite a failed permission-profile deny probe")

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
            json.dumps(suite(prompt="SKILL_INVOKED_CASE", should_invoke=True)),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=0, status="PASS")

        cases_path.write_text(
            json.dumps(suite(prompt="SKILL_INVOKED_WRAPPED_CASE", should_invoke=True)),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=0, status="PASS")

        cases_path.write_text(
            json.dumps(suite(prompt="SKILL_INVOKED_WINDOWS_CASE", should_invoke=True)),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=0, status="PASS")

        cases_path.write_text(
            json.dumps(suite(prompt="SKILL_LIST_ONLY_CASE", should_invoke=True)),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=1, status="FAIL")

        cases_path.write_text(
            json.dumps(suite(prompt="SKILL_SPOOF_CASE", should_invoke=True)),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=1, status="FAIL")

        cases_path.write_text(
            json.dumps(suite(prompt="NATIVE_SKILL_EVENT_CASE", should_invoke=True)),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=0, status="PASS")

        cases_path.write_text(
            json.dumps(suite(prompt="SKILL_INVOKED_CASE")),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=1, status="FAIL")

        cases_path.write_text(
            json.dumps(
                suite(
                    prompt="FINAL_ONLY_PASS_CASE",
                    ordered_markers=["alpha", "beta"],
                )
            ),
            encoding="utf-8",
        )
        assert_result(run(fake_codex, cases_path), returncode=0, status="PASS")

        cases_path.write_text(
            json.dumps(
                suite(
                    prompt="FINAL_ONLY_FAIL_CASE",
                    ordered_markers=["alpha", "beta"],
                )
            ),
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
            json.dumps(
                suite(
                    prompt="MODEL_CASE",
                    model_grader=True,
                    sandbox="workspace-write",
                    require_unchanged_workspace=False,
                )
            ),
            encoding="utf-8",
        )
        retained_parent = root / "retained-artifacts"
        isolated_result = run(
            fake_codex,
            cases_path,
            "--artifacts-dir",
            str(retained_parent),
        )
        assert_result(isolated_result, returncode=0, status="PASS")
        assert_isolated_invocations(
            isolated_result,
            expected_kinds=["behavior", "grader"],
            caller_codex_home=caller_codex_home,
        )
        retained_artifacts = Path(str(isolated_result[1]["artifacts_dir"]))
        if not retained_artifacts.is_dir():
            raise SystemExit("requested eval artifacts were not retained")
        if list(retained_artifacts.rglob("auth.json")):
            raise SystemExit("authentication was retained with eval artifacts")
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
            "    raise SystemExit(1)\n"
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
