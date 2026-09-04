#!/usr/bin/env python3
"""Validate a generated zero-to-hero handoff without product dependencies."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

CANONICAL_MANIFEST = Path("docs/00-meta/generated-files.manifest.yaml")
ACTIVE_EXECPLAN = Path("docs/implementation/EXECPLAN.md")
EXPECTED_REQUIRED_PATHS = frozenset(["__ZERO_TO_HERO_REQUIRED_PATHS__"])
EXPECTED_REFRESH_COMMAND = "__ZERO_TO_HERO_REFRESH_COMMAND__"
EXPECTED_REGENERATION_COMMAND = "__ZERO_TO_HERO_REGENERATION_COMMAND__"
EXPECTED_APPROVAL_BINDING = "__ZERO_TO_HERO_APPROVAL_BINDING__"
COMMAND_CONTRACT_START = "<!-- ZERO_TO_HERO:COMMANDS:START -->"
COMMAND_CONTRACT_END = "<!-- ZERO_TO_HERO:COMMANDS:END -->"
IMPLEMENTATION_COMPLETION_TOKEN = "Do not claim implementation completion"
REQUIRED_EXECPLAN_HEADINGS = frozenset(
    {
        "## purpose and user-visible outcome",
        "## repository orientation",
        "## scope and non-goals",
        "## milestones",
        "## progress",
        "## surprises and discoveries",
        "## decision log",
        "## validation",
        "## stop conditions",
        "## recovery and restart",
        "## outcomes and retrospective",
        "## done criteria",
    }
)


def sha256_path(path: Path) -> str | None:
    if not path.is_file() or path.is_symlink():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contained_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if (
        candidate.is_absolute()
        or not candidate.parts
        or ".." in candidate.parts
        or "\x00" in relative
    ):
        raise ValueError(f"unsafe manifest target path: {relative!r}")
    target = root / candidate
    cursor = root
    for part in candidate.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"manifest target traverses a symlink: {relative}")
    try:
        target.parent.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"manifest target escapes the repository: {relative}") from exc
    return target


def load_manifest(root: Path, errors: list[str]) -> dict[str, Any] | None:
    path = root / CANONICAL_MANIFEST
    if not path.is_file() or path.is_symlink():
        errors.append(f"missing canonical manifest: {CANONICAL_MANIFEST}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"canonical manifest is unreadable: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append("canonical manifest root must be an object")
        return None
    return data


def validate_manifest_contract(
    root: Path,
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    if manifest.get("schema_version") != 1:
        errors.append("manifest schema_version must be 1")
    if manifest.get("tool") != "zero-to-hero":
        errors.append("manifest tool must be zero-to-hero")
    if manifest.get("status") != "complete":
        errors.append("manifest status must be complete")
    selected_profiles = manifest.get("selected_profiles")
    if (
        not isinstance(selected_profiles, list)
        or not selected_profiles
        or not all(isinstance(item, str) and item for item in selected_profiles)
        or len(selected_profiles) != len(set(selected_profiles))
    ):
        errors.append("manifest selected_profiles must be a non-empty unique string list")
        selected_profiles = []
    validation = manifest.get("validation")
    if not isinstance(validation, dict) or validation.get("status") != "passed":
        errors.append("manifest validation status must be passed")
        validation = {}
    transaction = manifest.get("transaction")
    refresh_command = (
        str(transaction.get("refresh_command", ""))
        if isinstance(transaction, dict)
        else ""
    )
    if (
        not isinstance(transaction, dict)
        or transaction.get("mode") != "staged-atomic-with-rollback"
        or transaction.get("canonical_manifest") != CANONICAL_MANIFEST.as_posix()
        or transaction.get("rollback_on_commit_error") is not True
        or refresh_command != EXPECTED_REFRESH_COMMAND
    ):
        errors.append("manifest transaction is not a finalized atomic transaction")
    approved = manifest.get("approved_capabilities")
    approved_source = manifest.get("approved_capability_source")
    source_relative: str | None = None
    source_hash: str | None = None
    if not isinstance(approved, list) or not all(
        isinstance(item, str) and item for item in approved
    ):
        errors.append("manifest approved_capabilities must be a string list")
        approved = []
    if not isinstance(approved_source, dict):
        errors.append("manifest approved_capability_source must be an object")
        approved_source = {}
    expected_approved = EXPECTED_APPROVAL_BINDING["approved_capabilities"]
    expected_source = EXPECTED_APPROVAL_BINDING["source"]
    if approved != expected_approved:
        errors.append(
            "manifest approved capabilities differ from the embedded approval binding"
        )
    if approved_source != expected_source:
        errors.append(
            "manifest approved capability source differs from the embedded "
            "approval binding"
        )
    if approved:
        source_relative = approved_source.get("path")
        source_hash = approved_source.get("sha256")
        if not isinstance(source_relative, str) or not isinstance(source_hash, str):
            errors.append("approved capabilities require path-and-hash evidence")
        else:
            try:
                source_target = contained_path(root, source_relative)
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if sha256_path(source_target) != source_hash:
                    errors.append(
                        "approved capability evidence is missing or changed: "
                        f"{source_relative}"
                    )
    elif approved_source.get("path") is not None or approved_source.get("sha256") is not None:
        errors.append(
            "approved capability evidence must be null when no approval was selected"
        )

    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        errors.append("manifest files must be a non-empty array")
        return
    seen: set[str] = set()
    regeneration_commands: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"manifest file record {index} is not an object")
            continue
        relative = record.get("target_path")
        if not isinstance(relative, str) or not relative:
            errors.append(f"manifest file record {index} has no target_path")
            continue
        if relative in seen:
            errors.append(f"manifest target is duplicated: {relative}")
            continue
        seen.add(relative)
        regeneration_command = record.get("regeneration_command")
        if not isinstance(regeneration_command, str):
            errors.append(f"manifest file record {index} has no regeneration command")
        else:
            regeneration_commands.add(regeneration_command)
            if regeneration_command != EXPECTED_REGENERATION_COMMAND:
                errors.append(
                    "manifest regeneration command differs from the generated "
                    f"canonical replay: {relative}"
                )
        try:
            target = contained_path(root, relative)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        actual = sha256_path(target)
        if actual is None:
            errors.append(f"manifest target is missing, non-regular, or a symlink: {relative}")
            continue
        expected = record.get("post_write_sha256")
        if relative == CANONICAL_MANIFEST.as_posix():
            if expected is not None:
                errors.append("canonical manifest self-reference hash must be null")
        elif (
            not isinstance(expected, str)
            or len(expected) != 64
            or actual != expected
        ):
            errors.append(f"manifest hash mismatch: {relative}")
    if len(regeneration_commands) != 1:
        errors.append(
            "manifest records do not share one canonical regeneration command"
        )
    if (
        "__ZERO_TO_HERO_" in EXPECTED_REFRESH_COMMAND
        or "__ZERO_TO_HERO_" in EXPECTED_REGENERATION_COMMAND
    ):
        errors.append("generated validator has unresolved lifecycle-command markers")

    if "__ZERO_TO_HERO_REQUIRED_PATHS__" in EXPECTED_REQUIRED_PATHS:
        errors.append("generated validator has no embedded contract-selected path set")
    missing_required = sorted(EXPECTED_REQUIRED_PATHS - seen)
    extra_records = sorted(seen - EXPECTED_REQUIRED_PATHS)
    if missing_required:
        errors.append(
            "manifest omits contract-selected handoff artifacts: "
            + ", ".join(missing_required)
        )
    if extra_records:
        errors.append(
            "manifest contains artifacts outside the embedded contract selection: "
            + ", ".join(extra_records)
        )

    forbidden = validation.get("forbidden_artifacts_absent", [])
    if not isinstance(forbidden, list) or not all(
        isinstance(item, str) and item for item in forbidden
    ):
        errors.append("manifest forbidden_artifacts_absent must be a string list")
    else:
        for relative in forbidden:
            try:
                target = contained_path(root, relative)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if target.exists() or target.is_symlink():
                errors.append(f"profile-forbidden artifact is present: {relative}")

    execplan = root / ACTIVE_EXECPLAN
    if execplan.is_file() and not execplan.is_symlink():
        text = execplan.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        missing_headings = sorted(
            heading for heading in REQUIRED_EXECPLAN_HEADINGS if heading not in lowered
        )
        if missing_headings:
            errors.append(
                "active ExecPlan omits required sections: "
                + ", ".join(missing_headings)
            )
        for profile in selected_profiles:
            if profile not in text:
                errors.append(f"active ExecPlan omits selected profile: {profile}")
        if approved and source_relative and source_hash:
            if source_relative not in text or source_hash not in text:
                errors.append(
                    "active ExecPlan is not bound to the approved capability "
                    "evidence path and hash"
                )
        invented = invented_command_claims(text)
        if invented:
            errors.append(
                "active ExecPlan contains invented command claims: "
                + ", ".join(invented)
            )

    agents = root / "AGENTS.md"
    if agents.is_file() and not agents.is_symlink():
        agents_text = agents.read_text(encoding="utf-8", errors="ignore")
        for token in (
            "scripts/zero_to_hero_handoff_check.py",
            ACTIVE_EXECPLAN.as_posix(),
            IMPLEMENTATION_COMPLETION_TOKEN,
            COMMAND_CONTRACT_START,
            COMMAND_CONTRACT_END,
        ):
            if token not in agents_text:
                errors.append(f"AGENTS.md omits generated harness contract: {token}")
        if execplan.is_file() and not execplan.is_symlink():
            execplan_text = execplan.read_text(encoding="utf-8", errors="ignore")
            agents_block = command_contract(agents_text)
            execplan_block = command_contract(execplan_text)
            if agents_block is None or execplan_block is None:
                errors.append("AGENTS.md and ExecPlan require machine-owned command markers")
            elif agents_block != execplan_block:
                errors.append("AGENTS.md and ExecPlan command contracts differ")
        invented = invented_command_claims(agents_text)
        if invented:
            errors.append(
                "AGENTS.md contains invented command claims: "
                + ", ".join(invented)
            )

    source_map = root / "docs/00-meta/source-of-truth-map.yaml"
    if source_map.is_file() and not source_map.is_symlink():
        source_text = source_map.read_text(encoding="utf-8", errors="ignore")
        if ACTIVE_EXECPLAN.as_posix() not in source_text:
            errors.append("source-of-truth map does not identify the active ExecPlan")


def command_contract(text: str) -> str | None:
    start = text.find(COMMAND_CONTRACT_START)
    end = text.find(COMMAND_CONTRACT_END, start)
    if start < 0 or end < 0:
        return None
    return text[start : end + len(COMMAND_CONTRACT_END)].strip()


def markdown_fenced_blocks(text: str) -> list[tuple[str, str]]:
    """Return CommonMark backtick and tilde fenced blocks."""

    lines = text.splitlines()
    blocks: list[tuple[str, str]] = []
    index = 0
    opening_pattern = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")
    while index < len(lines):
        opening = opening_pattern.match(lines[index])
        if opening is None:
            index += 1
            continue
        fence = opening.group(1)
        language = opening.group(2).strip()
        marker = re.escape(fence[0])
        closing_pattern = re.compile(
            rf"^[ \t]{{0,3}}{marker}{{{len(fence)},}}[ \t]*$"
        )
        index += 1
        body: list[str] = []
        while index < len(lines) and not closing_pattern.match(lines[index]):
            body.append(lines[index])
            index += 1
        blocks.append((language, "\n".join(body)))
        if index < len(lines):
            index += 1
    return blocks


def invented_command_claims(text: str) -> list[str]:
    block = command_contract(text) or ""
    outside = text.replace(block, "", 1)
    allowed = {
        value.strip()
        for value in re.findall(r"`([^`\n]+)`", block)
    }
    command_prefix = re.compile(
        r"^(?:(?:npm|npx|pnpm|yarn|bun|python(?:3)?|py|make|just|git|"
        r"cargo|go|gradle|mvn|pio|uv|poetry|ruff|pytest|mypy|pyright|"
        r"bash|sh|zsh|env|cmd|powershell|pwsh|sudo|doas|command|builtin|"
        r"exec|cd)(?:\s|$)|\./\S+|/(?:usr/)?bin/\S+|"
        r"(?:[A-Za-z_][A-Za-z0-9_]*=[^\s]+\s+)+\S+)"
    )
    candidates = [
        (value.strip(), False)
        for value in re.findall(r"`([^`\n]+)`", outside)
    ]
    shell_languages = {
        "bash",
        "cmd",
        "console",
        "powershell",
        "ps1",
        "pwsh",
        "sh",
        "shell",
        "zsh",
    }
    for info_string, body in markdown_fenced_blocks(outside):
        language = info_string.split(maxsplit=1)[0].lower()
        shell_context = language in shell_languages
        for line in body.splitlines():
            candidate = re.sub(r"^\$\s+", "", line.strip())
            if candidate and not candidate.startswith("#"):
                candidates.append((candidate, shell_context))
    return sorted(
        {
            candidate
            for candidate, shell_context in candidates
            if (shell_context or command_prefix.match(candidate))
            and candidate not in allowed
        }
    )


def validate_git_diff(root: Path, errors: list[str]) -> None:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        commands = (
            ["git", "-C", str(root), "diff", "--check"],
            ["git", "-C", str(root), "diff", "--cached", "--check"],
        )
        results = [
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )
            for command in commands
        ]
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"Git whitespace checks could not run: {exc}")
        return
    labels = ("git diff --check", "git diff --cached --check")
    for label, result in zip(labels, results):
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            errors.append(
                f"{label} failed" + (f": {detail[:500]}" if detail else "")
            )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []
    if not root.is_dir():
        errors.append(f"repository root is not a directory: {root}")
    else:
        manifest = load_manifest(root, errors)
        if manifest is not None:
            validate_manifest_contract(root, manifest, errors)
        validate_git_diff(root, errors)
    report = {
        "tool": "zero-to-hero-generated-handoff-validator",
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "handoff baseline integrity only; compose this gate with product checks "
            "before claiming product implementation complete"
        ),
        "repo": str(root),
        "checks": [
            "finalized-manifest",
            "contract-selected-record-set-and-artifact-hashes",
            "profile-forbidden-artifact-absence",
            "active-execplan-contract",
            "generated-agent-harness-contract",
            "unstaged-and-staged-git-whitespace",
        ],
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
