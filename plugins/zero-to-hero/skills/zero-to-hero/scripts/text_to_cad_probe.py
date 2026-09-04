#!/usr/bin/env python3
"""Read-only compatibility probe for earthtojake/text-to-cad v0.3.9 skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

sys.dont_write_bytecode = True

AUDITED_SOURCE = "earthtojake/text-to-cad"
AUDITED_VERSION = "0.3.9"
AUDITED_RANGE = "==0.3.9"
AUDITED_TAG = "0.3.9"
AUDITED_COMMIT = "fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423"
AUDITED_SOURCE_COMMIT = "ac2659a1e7256b030a87dd4d45a37dcdccce6b45"
RELEASED_AT = "2026-07-10T19:58:16Z"
AUDITED_DATE = "2026-07-22"
MINIMUM_PYTHON = (3, 12)

OPERATIONAL = "operational"
UNAVAILABLE = "unavailable"
INCOMPATIBLE = "incompatible"
SKIPPED = "skipped"
STATUSES = (OPERATIONAL, UNAVAILABLE, INCOMPATIBLE, SKIPPED)

SKILL_NAMES = ("cad", "step-parts", "cad-viewer", "urdf", "srdf", "sdf")
SCOPE_PRIORITY = {"project": 0, "local": 1, "global": 2, "unknown": 3}
EXPECTED_SKILL_HASHES: dict[str, dict[str, str]] = {
    "cad": {
        "skills_cli": "b610dd9fa7db52306080304f10f7a08c9625e42a189de9e34040f4a956951196",
        "portable_tree_sha256": "8f5a957a4d13e68478ee3c44e2eedafefded6ca8cb1b2f811d863738e322bae6",
    },
    "cad-viewer": {
        "skills_cli": "a7e9c02d2bfa838c20f6926c8b6d3983163fae5d756c6a6b277139f638223283",
        "portable_tree_sha256": "1071d71311718fa0f9526d72870af2ae51885b6f1d67b659d5cec99369ee20a7",
    },
    "step-parts": {
        "skills_cli": "6e915d1d1e1b2da6d5fae2dd412371b6d500145816da2ae203eed1b5ad6eacfc",
        "portable_tree_sha256": "9a466691dce30ddd24704dcc8edd3065afcc5354ad7d65224d35a7176cd03b67",
    },
    "urdf": {
        "skills_cli": "a48999f1d3868b03412d7ae6e0ba9fae44e8d293bb04a2d929959ed2f4fb5441",
        "portable_tree_sha256": "9f7bb364c90e1986d0d53e332c7ccb7e2273577e0255442e10baf9df296ffb30",
    },
    "srdf": {
        "skills_cli": "5597782c3ab7afc7f3e1fc8474d5853e64bf0abcef229b62db8b46417efa13d2",
        "portable_tree_sha256": "00d7f71c36b7049b546ec949e86c711493f9aef7de07a88b5a865760e527685e",
    },
    "sdf": {
        "skills_cli": "dd508dc1478fce583cd17eecca255532950ade368468aa36dee3fb5b8ffbfdef",
        "portable_tree_sha256": "bf74d5db299e477ebc54d425e35ea80374c1ad023567e5c3ca2760329a3ab978",
    },
}

INTERFACES: dict[str, dict[str, Any]] = {
    "cad.step": {
        "skill": "cad",
        "launcher": "scripts/step",
        "command": "python <cad>/scripts/step SOURCE.py=OUTPUT.step",
        "required_help_tokens": [
            "--kind",
            "--stl",
            "--3mf",
            "--glb",
            "--skip-step-write",
            "--force",
            "--mesh-tolerance",
            "--mesh-angular-tolerance",
        ],
        "generator": "gen_step()",
    },
    "cad.inspect": {
        "skill": "cad",
        "launcher": "scripts/inspect",
        "command": (
            "python <cad>/scripts/inspect refs OUTPUT.step "
            "--facts --planes --positioning"
        ),
        "required_help_tokens": [
            "refs",
            "diff",
            "frame",
            "measure",
            "align",
            "worker",
            "batch",
        ],
        "subcommands": {
            "measure": "measure ENTRY --from REF --to REF [--axis x|y|z]",
            "align": (
                "align ENTRY --moving REF --target REF "
                "[--mode flush|center] [--offset FLOAT] [--axis x|y|z]"
            ),
            "frame": "frame ENTRY [SELECTOR]",
            "diff": "diff LEFT.step RIGHT.step",
        },
    },
    "cad.snapshot": {
        "skill": "cad",
        "launcher": "scripts/snapshot",
        "command": (
            "python <cad>/scripts/snapshot --input OUTPUT.step "
            "--output SNAPSHOT.png --appearance workbench"
        ),
        "required_help_tokens": [
            "--job",
            "--input",
            "--output",
            "--appearance",
            "--display",
            "--focus",
            "--hide",
            "--camera",
            "--size-profile",
            "--view-labels",
        ],
    },
    "step-parts.download": {
        "skill": "step-parts",
        "launcher": "scripts/download_step_part.py",
        "command": (
            "python <step-parts>/scripts/download_step_part.py QUERY "
            "--download --out-dir DIR"
        ),
        "required_help_tokens": [
            "--id",
            "--origin",
            "--download",
            "--all",
            "--out-dir",
            "--filename",
            "--overwrite",
            "--limit",
            "--page",
            "--tag",
            "--category",
            "--family",
            "--standard",
        ],
    },
    "cad-viewer.agent-start": {
        "skill": "cad-viewer",
        "launcher": "scripts/viewer/package.json",
        "command": (
            "npm --prefix <cad-viewer>/scripts/viewer run agent:start -- "
            "--host 127.0.0.1 --dir ABSOLUTE_ROOT"
        ),
        "required_help_tokens": ["--host", "--dir"],
    },
    "urdf.generate": {
        "skill": "urdf",
        "launcher": "scripts/urdf",
        "command": "python <urdf>/scripts/urdf SOURCE.py=OUTPUT.urdf",
        "required_help_tokens": ["--output", "gen_urdf()", "SOURCE.py=OUTPUT.urdf"],
        "generator": "gen_urdf()",
    },
    "srdf.generate": {
        "skill": "srdf",
        "launcher": "scripts/srdf",
        "command": "python <srdf>/scripts/srdf SOURCE.py=OUTPUT.srdf",
        "required_help_tokens": ["--output", "gen_srdf()", "SOURCE.py=OUTPUT.srdf"],
        "generator": "gen_srdf()",
    },
    "sdf.generate": {
        "skill": "sdf",
        "launcher": "scripts/sdf",
        "command": "python <sdf>/scripts/sdf SOURCE.py=OUTPUT.sdf --gz-check auto",
        "required_help_tokens": [
            "--output",
            "--gz-check",
            "--strict",
            "gen_sdf()",
            "SOURCE.py=OUTPUT.sdf",
        ],
        "generator": "gen_sdf()",
    },
}

PYTHON_IMPORTS: dict[str, dict[str, list[str]]] = {
    "cad": {
        "modules": ["build123d", "OCP", "playwright", "cadpy.catalog"],
        "paths": ["scripts/packages/cadpy/src"],
    },
    "step-parts": {
        "modules": ["hashlib", "urllib.request"],
        "paths": [],
    },
    "urdf": {
        "modules": ["cadpy_metadata"],
        "paths": ["scripts/packages/cadpy_metadata/src"],
    },
    "srdf": {
        "modules": ["cadpy_metadata"],
        "paths": ["scripts/packages/cadpy_metadata/src"],
    },
    "sdf": {
        "modules": ["cadpy_metadata"],
        "paths": ["scripts/packages/cadpy_metadata/src"],
    },
}


def audited_contract() -> dict[str, Any]:
    return {
        "source": AUDITED_SOURCE,
        "tested_compatibility_range": AUDITED_RANGE,
        "version": AUDITED_VERSION,
        "tag": AUDITED_TAG,
        "commit": AUDITED_COMMIT,
        "source_commit": AUDITED_SOURCE_COMMIT,
        "released_at": RELEASED_AT,
        "audited_date": AUDITED_DATE,
        "minimum_python": ".".join(str(part) for part in MINIMUM_PYTHON),
        "skills": list(SKILL_NAMES),
        "skill_hashes": EXPECTED_SKILL_HASHES,
        "interfaces": INTERFACES,
        "safety_boundary": {
            "mode": "read-only compatibility probe",
            "network_requests": False,
            "generation_commands_executed": False,
            "physical_actions_executed": False,
            "excluded_actions": [
                "fabrication",
                "printing",
                "machine upload",
                "firmware flashing",
                "deployment",
                "robot actuation",
            ],
        },
    }


def _bounded_text(value: str | bytes | None, limit: int = 8000) -> str:
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = value or ""
    return text[-limit:]


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except (OSError, ProcessLookupError):
        process.kill()


def run_bounded(
    command: Sequence[str],
    *,
    cwd: Path | None,
    timeout: int,
    env_overrides: Mapping[str, str | None] | None = None,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for key, value in (env_overrides or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    popen_args: dict[str, Any] = {
        "cwd": str(cwd) if cwd else None,
        "env": env,
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    if os.name == "posix":
        popen_args["start_new_session"] = True
    elif hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        popen_args["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        process = subprocess.Popen(list(command), **popen_args)
    except OSError as exc:
        return {
            "command": list(command),
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
            "launch_error": type(exc).__name__,
        }
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return {
            "command": list(command),
            "returncode": process.returncode,
            "stdout": _bounded_text(stdout),
            "stderr": _bounded_text(stderr),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        _terminate_process(process)
        stdout, stderr = process.communicate()
        return {
            "command": list(command),
            "returncode": process.returncode,
            "stdout": _bounded_text(stdout or exc.stdout),
            "stderr": _bounded_text(stderr or exc.stderr),
            "timed_out": True,
            "timeout_seconds": timeout,
        }


def _resolve_executable(command: str, *, env: Mapping[str, str] | None = None) -> str | None:
    candidate = Path(command).expanduser()
    if candidate.parent != Path(".") or candidate.is_absolute():
        resolved = candidate.resolve()
        return str(resolved) if resolved.is_file() and os.access(resolved, os.X_OK) else None
    path_value = (env or os.environ).get("PATH")
    return shutil.which(command, path=path_value)


def _status(
    status: str,
    reason_code: str,
    message: str,
    **extra: Any,
) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(f"Unsupported probe status: {status}")
    return {
        "status": status,
        "reason_code": reason_code,
        "message": message,
        **extra,
    }


def _skipped_check(name: str, reason: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": SKIPPED,
        "reason_code": "prerequisite_not_operational",
        "message": reason,
    }


def compute_portable_tree_hash(skill_path: Path) -> str:
    """Hash relative paths and contents with a locale-independent ordering."""

    root = skill_path.resolve()
    files: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if ".git" in relative.parts or "node_modules" in relative.parts:
            continue
        files.append((relative.as_posix(), path))
    digest = hashlib.sha256()
    for relative, path in sorted(files, key=lambda item: item[0]):
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _default_discovery_roots(repo: Path, home: Path) -> list[tuple[str, Path]]:
    return [
        ("project", repo / ".agents" / "skills"),
        ("project", repo / ".codex" / "skills"),
        ("local", repo / "skills"),
        ("global", home / ".agents" / "skills"),
        ("global", home / ".codex" / "skills"),
    ]


def _record_filesystem_candidates(
    records: list[dict[str, Any]],
    roots: Sequence[tuple[str, Path]],
) -> None:
    for scope, raw_root in roots:
        root = raw_root.expanduser().resolve()
        for name in SKILL_NAMES:
            candidate = root if root.name == name else root / name
            if candidate.is_dir():
                records.append(
                    {
                        "name": name,
                        "path": str(candidate.resolve()),
                        "scope": scope if scope in SCOPE_PRIORITY else "unknown",
                        "discovered_by": "filesystem",
                    }
                )


def _skills_cli_base(skills_command: str | None) -> list[str] | None:
    if skills_command:
        resolved = _resolve_executable(skills_command)
        return [resolved] if resolved else None
    direct = _resolve_executable("skills")
    if direct:
        return [direct]
    npx = _resolve_executable("npx")
    if npx:
        return [npx, "--no-install", "skills"]
    return None


def _parse_skill_list(payload: Any, *, default_scope: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError("skills list JSON must be an array")
    records: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name", ""))
        if name not in SKILL_NAMES:
            continue
        path_text = str(item.get("path", ""))
        if not path_text:
            continue
        scope = str(item.get("scope", default_scope))
        records.append(
            {
                "name": name,
                "path": str(Path(path_text).expanduser().resolve()),
                "scope": scope if scope in SCOPE_PRIORITY else default_scope,
                "discovered_by": "skills_cli",
                "agents": list(item.get("agents", []))
                if isinstance(item.get("agents"), list)
                else [],
            }
        )
    return records


def discover_skills(
    repo: Path,
    *,
    home: Path,
    timeout: int,
    roots: Sequence[tuple[str, Path]] | None = None,
    skills_command: str | None = None,
    use_skills_cli: bool = True,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    filesystem_roots = (
        list(roots) if roots is not None else _default_discovery_roots(repo, home)
    )
    _record_filesystem_candidates(records, filesystem_roots)

    cli_probes: list[dict[str, Any]] = []
    cli_base = _skills_cli_base(skills_command) if use_skills_cli else None
    if use_skills_cli and cli_base is None:
        cli_probes.append(
            _status(
                SKIPPED,
                "skills_cli_unavailable",
                (
                    "No already-installed skills CLI could be resolved; "
                    "filesystem discovery continued."
                ),
            )
        )
    elif cli_base is not None:
        for default_scope, extra_args in (("project", []), ("global", ["--global"])):
            command = [*cli_base, "list", *extra_args, "--json"]
            run = run_bounded(command, cwd=repo, timeout=timeout)
            if run["timed_out"]:
                cli_probes.append(
                    _status(
                        SKIPPED,
                        "skills_cli_timeout",
                        f"Skills CLI {default_scope} discovery timed out.",
                        scope=default_scope,
                        execution=run,
                    )
                )
                continue
            if run["returncode"] != 0:
                cli_probes.append(
                    _status(
                        SKIPPED,
                        "skills_cli_failed",
                        f"Skills CLI {default_scope} discovery did not complete.",
                        scope=default_scope,
                        execution=run,
                    )
                )
                continue
            try:
                payload = json.loads(run["stdout"])
                parsed = _parse_skill_list(payload, default_scope=default_scope)
            except (json.JSONDecodeError, ValueError) as exc:
                cli_probes.append(
                    _status(
                        SKIPPED,
                        "skills_cli_invalid_json",
                        f"Skills CLI {default_scope} discovery returned invalid JSON: {exc}",
                        scope=default_scope,
                        execution=run,
                    )
                )
                continue
            records.extend(parsed)
            cli_probes.append(
                _status(
                    OPERATIONAL,
                    "skills_cli_listed",
                    f"Skills CLI {default_scope} discovery completed.",
                    scope=default_scope,
                    count=len(parsed),
                )
            )

    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (str(record["name"]), str(Path(str(record["path"])).resolve()))
        previous = unique.get(key)
        if previous is None:
            unique[key] = record
            continue
        previous_scope = str(previous.get("scope", "unknown"))
        current_scope = str(record.get("scope", "unknown"))
        if SCOPE_PRIORITY.get(current_scope, 3) < SCOPE_PRIORITY.get(previous_scope, 3):
            unique[key] = record

    grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in SKILL_NAMES}
    for record in unique.values():
        grouped[str(record["name"])].append(record)
    selected: dict[str, dict[str, Any] | None] = {}
    for name, candidates in grouped.items():
        candidates.sort(
            key=lambda item: (
                SCOPE_PRIORITY.get(str(item.get("scope", "unknown")), 3),
                0 if item.get("discovered_by") == "filesystem" else 1,
                str(item.get("path", "")),
            )
        )
        selected[name] = candidates[0] if candidates else None

    discovered_count = sum(1 for value in selected.values() if value is not None)
    return {
        "status": OPERATIONAL if discovered_count else UNAVAILABLE,
        "reason_code": "skills_discovered" if discovered_count else "skills_not_found",
        "message": (
            f"Discovered {discovered_count} selected text-to-CAD skill path(s)."
            if discovered_count
            else "No text-to-CAD skill paths were discovered."
        ),
        "filesystem_roots": [
            {"scope": scope, "path": str(path.expanduser().resolve())}
            for scope, path in filesystem_roots
        ],
        "cli_probes": cli_probes,
        "candidates": grouped,
        "selected": selected,
    }


def _read_lock_entry(
    repo: Path,
    skill_name: str,
    skill_path: Path,
    home: Path,
) -> tuple[Path | None, Mapping[str, Any] | None, str | None]:
    resolved_repo = repo.resolve()
    resolved_skill = skill_path.resolve()
    lock_candidates: list[Path] = []
    for ancestor in list(skill_path.resolve().parents)[:4]:
        lock_candidates.append(ancestor / "skills-lock.json")
    try:
        resolved_skill.relative_to(resolved_repo)
        lock_candidates.append(resolved_repo / "skills-lock.json")
    except ValueError:
        pass
    lock_candidates.extend(
        [
            home / "skills-lock.json",
            home / ".agents" / "skills-lock.json",
            home / ".codex" / "skills-lock.json",
        ]
    )
    seen: set[Path] = set()
    for lock_path in lock_candidates:
        resolved = lock_path.expanduser().resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return resolved, None, f"{type(exc).__name__}: {exc}"
        skills = payload.get("skills") if isinstance(payload, Mapping) else None
        entry = skills.get(skill_name) if isinstance(skills, Mapping) else None
        if isinstance(entry, Mapping):
            return resolved, entry, None
    return None, None, None


def _normalize_ref(value: str) -> str:
    normalized = value.strip()
    for prefix in ("refs/tags/", "v"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized


def probe_provenance(
    repo: Path,
    skill_name: str,
    skill_path: Path,
    *,
    home: Path,
    expected_hashes: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    if not skill_path.is_dir():
        return _status(
            UNAVAILABLE,
            "skill_path_missing",
            f"Discovered {skill_name} path is not a directory: {skill_path}",
            checks=checks,
        )
    checks.append(
        _status(OPERATIONAL, "skill_path_exists", "Discovered skill directory exists.", name="path")
    )
    skill_markdown = skill_path / "SKILL.md"
    if not skill_markdown.is_file():
        checks.append(
            _status(
                INCOMPATIBLE,
                "skill_manifest_missing",
                f"{skill_name} does not contain SKILL.md.",
                name="skill_manifest",
            )
        )
        return _status(
            INCOMPATIBLE,
            "skill_manifest_missing",
            f"{skill_name} is not a complete installed skill.",
            checks=checks,
        )
    checks.append(
        _status(
            OPERATIONAL,
            "skill_manifest_exists",
            "SKILL.md exists.",
            name="skill_manifest",
            path=str(skill_markdown),
        )
    )

    try:
        portable_hash = compute_portable_tree_hash(skill_path)
    except OSError as exc:
        checks.append(
            _status(
                UNAVAILABLE,
                "skill_hash_read_failed",
                f"Could not hash {skill_name}: {exc}",
                name="portable_tree_sha256",
            )
        )
        return _status(
            UNAVAILABLE,
            "skill_hash_read_failed",
            f"Could not verify {skill_name} content.",
            checks=checks,
        )

    expected = expected_hashes.get(skill_name, {})
    expected_portable = expected.get("portable_tree_sha256")
    if expected_portable is None:
        checks.append(
            _status(
                SKIPPED,
                "audited_content_hash_unavailable",
                "No audited portable content hash was supplied.",
                name="portable_tree_sha256",
                actual=portable_hash,
            )
        )
    elif portable_hash != expected_portable:
        checks.append(
            _status(
                INCOMPATIBLE,
                "audited_content_hash_mismatch",
                f"{skill_name} content does not match audited v{AUDITED_VERSION}.",
                name="portable_tree_sha256",
                expected=expected_portable,
                actual=portable_hash,
            )
        )
    else:
        checks.append(
            _status(
                OPERATIONAL,
                "audited_content_hash_matches",
                f"{skill_name} content matches the audited v{AUDITED_VERSION} tree.",
                name="portable_tree_sha256",
                expected=expected_portable,
                actual=portable_hash,
            )
        )

    lock_path, lock_entry, lock_error = _read_lock_entry(
        repo, skill_name, skill_path, home
    )
    if lock_error:
        checks.append(
            _status(
                INCOMPATIBLE,
                "skills_lock_invalid",
                f"Could not read {lock_path}: {lock_error}",
                name="skills_lock",
                path=str(lock_path),
            )
        )
    elif lock_entry is None:
        checks.extend(
            [
                _status(
                    SKIPPED,
                    "skills_lock_entry_absent",
                    (
                        "No skills-lock.json entry was available; audited content "
                        "hash remains authoritative."
                    ),
                    name="lock_source",
                ),
                _status(
                    SKIPPED,
                    "skills_lock_entry_absent",
                    (
                        "No skills-lock.json entry was available; audited content "
                        "hash remains authoritative."
                    ),
                    name="lock_ref",
                ),
                _status(
                    SKIPPED,
                    "skills_lock_entry_absent",
                    (
                        "No skills-lock.json entry was available; audited content "
                        "hash remains authoritative."
                    ),
                    name="lock_hash",
                ),
                _status(
                    SKIPPED,
                    "skills_lock_entry_absent",
                    (
                        "No skills-lock.json entry was available; the installed "
                        "skill path was verified directly."
                    ),
                    name="lock_skill_path",
                ),
            ]
        )
    else:
        source = lock_entry.get("source")
        if source is None:
            checks.append(
                _status(
                    SKIPPED,
                    "lock_source_absent",
                    "The lock entry does not record a source.",
                    name="lock_source",
                    lock_path=str(lock_path),
                )
            )
        elif str(source) != AUDITED_SOURCE:
            checks.append(
                _status(
                    INCOMPATIBLE,
                    "lock_source_mismatch",
                    f"Lock source {source!r} does not match {AUDITED_SOURCE!r}.",
                    name="lock_source",
                    expected=AUDITED_SOURCE,
                    actual=str(source),
                    lock_path=str(lock_path),
                )
            )
        else:
            checks.append(
                _status(
                    OPERATIONAL,
                    "lock_source_matches",
                    "Lock source matches the audited repository.",
                    name="lock_source",
                    actual=str(source),
                    lock_path=str(lock_path),
                )
            )

        ref = lock_entry.get("ref")
        if ref is None:
            checks.append(
                _status(
                    SKIPPED,
                    "lock_ref_absent",
                    "The lock entry does not record a tag ref.",
                    name="lock_ref",
                    lock_path=str(lock_path),
                )
            )
        elif _normalize_ref(str(ref)) != AUDITED_VERSION:
            checks.append(
                _status(
                    INCOMPATIBLE,
                    "lock_ref_mismatch",
                    f"Lock ref {ref!r} is outside the audited {AUDITED_RANGE} range.",
                    name="lock_ref",
                    expected=AUDITED_VERSION,
                    actual=str(ref),
                    lock_path=str(lock_path),
                )
            )
        else:
            checks.append(
                _status(
                    OPERATIONAL,
                    "lock_ref_matches",
                    "Lock ref matches the audited tag.",
                    name="lock_ref",
                    actual=str(ref),
                    lock_path=str(lock_path),
                )
            )

        recorded_hash = lock_entry.get("computedHash")
        expected_cli_hash = expected.get("skills_cli")
        if recorded_hash is None:
            checks.append(
                _status(
                    SKIPPED,
                    "lock_hash_absent",
                    "The lock entry does not record a skills CLI hash.",
                    name="lock_hash",
                    lock_path=str(lock_path),
                )
            )
        elif expected_cli_hash is None:
            checks.append(
                _status(
                    SKIPPED,
                    "audited_lock_hash_unavailable",
                    "No audited skills CLI hash was supplied for comparison.",
                    name="lock_hash",
                    actual=str(recorded_hash),
                    lock_path=str(lock_path),
                )
            )
        elif str(recorded_hash) != expected_cli_hash:
            checks.append(
                _status(
                    INCOMPATIBLE,
                    "lock_hash_mismatch",
                    f"{skill_name} lock hash does not match audited v{AUDITED_VERSION}.",
                    name="lock_hash",
                    expected=expected_cli_hash,
                    actual=str(recorded_hash),
                    lock_path=str(lock_path),
                )
            )
        else:
            checks.append(
                _status(
                    OPERATIONAL,
                    "lock_hash_matches",
                    "Lock hash matches the audited skills CLI hash.",
                    name="lock_hash",
                    expected=expected_cli_hash,
                    actual=str(recorded_hash),
                    lock_path=str(lock_path),
                )
            )

        recorded_skill_path = lock_entry.get("skillPath")
        expected_skill_path = f"skills/{skill_name}/SKILL.md"
        if recorded_skill_path is None:
            checks.append(
                _status(
                    SKIPPED,
                    "lock_skill_path_absent",
                    "The lock entry does not record its upstream skill path.",
                    name="lock_skill_path",
                    lock_path=str(lock_path),
                )
            )
        elif str(recorded_skill_path).replace("\\", "/") != expected_skill_path:
            checks.append(
                _status(
                    INCOMPATIBLE,
                    "lock_skill_path_mismatch",
                    f"{skill_name} lock entry points to an unexpected upstream path.",
                    name="lock_skill_path",
                    expected=expected_skill_path,
                    actual=str(recorded_skill_path),
                    lock_path=str(lock_path),
                )
            )
        else:
            checks.append(
                _status(
                    OPERATIONAL,
                    "lock_skill_path_matches",
                    "Lock entry points to the audited upstream skill path.",
                    name="lock_skill_path",
                    expected=expected_skill_path,
                    actual=str(recorded_skill_path),
                    lock_path=str(lock_path),
                )
            )

    statuses = [str(check["status"]) for check in checks]
    if INCOMPATIBLE in statuses:
        result_status = INCOMPATIBLE
        reason = "provenance_incompatible"
        message = f"{skill_name} provenance does not match audited v{AUDITED_VERSION}."
    elif UNAVAILABLE in statuses:
        result_status = UNAVAILABLE
        reason = "provenance_unavailable"
        message = f"{skill_name} provenance could not be fully read."
    elif expected_portable is None:
        result_status = SKIPPED
        reason = "provenance_unverified"
        message = f"{skill_name} has no audited content hash."
    else:
        result_status = OPERATIONAL
        reason = "provenance_verified"
        message = f"{skill_name} path and audited content were verified."
    return _status(
        result_status,
        reason,
        message,
        skill_path=str(skill_path),
        lock_path=str(lock_path) if lock_path else None,
        lock_entry=dict(lock_entry) if lock_entry else None,
        checks=checks,
    )


def _parse_json_line(output: str) -> Mapping[str, Any] | None:
    for line in reversed(output.splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            return payload
    return None


def _single_line_python(source: str) -> str:
    """Keep ``python -c`` payloads safe to forward through Windows batch proxies."""

    return f"exec({source!r})"


def probe_python_runtime(python_command: str, *, timeout: int) -> dict[str, Any]:
    executable = _resolve_executable(python_command)
    if executable is None:
        return _status(
            UNAVAILABLE,
            "python_not_found",
            f"Python command {python_command!r} was not found.",
            minimum_version=list(MINIMUM_PYTHON),
        )
    code = _single_line_python(
        "import json,sys\n"
        "PROBE_KIND='text-to-cad-python-runtime'\n"
        "print(json.dumps({'probe':PROBE_KIND,'version':list(sys.version_info[:3]),"
        "'executable':sys.executable}))"
    )
    run = run_bounded([executable, "-c", code], cwd=None, timeout=timeout)
    run["command"] = [executable, "-c", "<python-runtime-probe>"]
    if run["timed_out"]:
        return _status(
            UNAVAILABLE,
            "python_version_timeout",
            "Python version probe timed out.",
            executable=executable,
            execution=run,
        )
    if run["returncode"] != 0:
        return _status(
            UNAVAILABLE,
            "python_version_failed",
            "Python version probe failed.",
            executable=executable,
            execution=run,
        )
    payload = _parse_json_line(run["stdout"])
    raw_version = payload.get("version") if payload else None
    if (
        not isinstance(raw_version, list)
        or len(raw_version) < 2
        or not all(isinstance(part, int) for part in raw_version[:2])
    ):
        return _status(
            INCOMPATIBLE,
            "python_version_unrecognized",
            "Python version probe did not return the audited JSON shape.",
            executable=executable,
            execution=run,
        )
    version = tuple(int(part) for part in raw_version[:3])
    if version[:2] < MINIMUM_PYTHON:
        return _status(
            INCOMPATIBLE,
            "python_version_unsupported",
            (
                f"Detected Python {'.'.join(map(str, version))}; text-to-CAD "
                f"v{AUDITED_VERSION} requires Python "
                f"{'.'.join(map(str, MINIMUM_PYTHON))}+."
            ),
            executable=executable,
            detected_version=list(version),
            minimum_version=list(MINIMUM_PYTHON),
            execution=run,
        )
    return _status(
        OPERATIONAL,
        "python_version_supported",
        f"Detected supported Python {'.'.join(map(str, version))}.",
        executable=executable,
        detected_version=list(version),
        minimum_version=list(MINIMUM_PYTHON),
    )


def probe_python_imports(
    python_runtime: Mapping[str, Any],
    *,
    modules: Sequence[str],
    paths: Sequence[Path],
    timeout: int,
) -> dict[str, Any]:
    if python_runtime.get("status") != OPERATIONAL:
        return _status(
            SKIPPED,
            "python_runtime_not_operational",
            "Import probe was skipped because the selected Python is not operational.",
            modules=list(modules),
            paths=[str(path) for path in paths],
        )
    executable = str(python_runtime["executable"])
    code = _single_line_python(
        "import importlib,json,sys\n"
        "PROBE_KIND='text-to-cad-python-imports'\n"
        "modules=json.loads(sys.argv[1]); paths=json.loads(sys.argv[2])\n"
        "for value in reversed(paths): sys.path.insert(0,value)\n"
        "loaded=[]; missing=[]\n"
        "for name in modules:\n"
        "  try: importlib.import_module(name); loaded.append(name)\n"
        "  except Exception as exc: missing.append({'module':name,'error':"
        "type(exc).__name__+': '+str(exc)})\n"
        "print(json.dumps({'probe':PROBE_KIND,'loaded':loaded,'missing':missing}))"
    )
    command = [
        executable,
        "-c",
        code,
        json.dumps(list(modules)),
        json.dumps([str(path) for path in paths]),
    ]
    run = run_bounded(command, cwd=None, timeout=timeout)
    run["command"] = [executable, "-c", "<python-import-probe>", *modules]
    if run["timed_out"]:
        return _status(
            UNAVAILABLE,
            "python_import_timeout",
            "Required Python import probe timed out.",
            modules=list(modules),
            execution=run,
        )
    if run["returncode"] != 0:
        return _status(
            UNAVAILABLE,
            "python_import_probe_failed",
            "Required Python import probe failed.",
            modules=list(modules),
            execution=run,
        )
    payload = _parse_json_line(run["stdout"])
    if payload is None or not isinstance(payload.get("missing"), list):
        return _status(
            INCOMPATIBLE,
            "python_import_output_unrecognized",
            "Python import probe did not return the audited JSON shape.",
            modules=list(modules),
            execution=run,
        )
    missing = list(payload["missing"])
    if missing:
        return _status(
            UNAVAILABLE,
            "python_dependencies_missing",
            "Required text-to-CAD Python imports are unavailable.",
            modules=list(modules),
            loaded=list(payload.get("loaded", [])),
            missing=missing,
        )
    return _status(
        OPERATIONAL,
        "python_dependencies_imported",
        "Required Python imports succeeded.",
        modules=list(modules),
        loaded=list(payload.get("loaded", [])),
    )


def probe_help(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout: int,
    required_tokens: Sequence[str],
    name: str,
) -> dict[str, Any]:
    run = run_bounded(command, cwd=cwd, timeout=timeout)
    if run["timed_out"]:
        return _status(
            INCOMPATIBLE,
            "launcher_help_timeout",
            f"{name} help probe timed out.",
            name=name,
            execution=run,
        )
    if run["returncode"] != 0:
        output = f"{run['stdout']}\n{run['stderr']}"
        missing_dependency = "ModuleNotFoundError" in output or "No module named" in output
        return _status(
            UNAVAILABLE if missing_dependency else INCOMPATIBLE,
            "launcher_dependency_missing" if missing_dependency else "launcher_help_failed",
            (
                f"{name} help probe could not import a required dependency."
                if missing_dependency
                else f"{name} help probe failed."
            ),
            name=name,
            execution=run,
        )
    output = f"{run['stdout']}\n{run['stderr']}"
    missing_tokens = [token for token in required_tokens if token not in output]
    if missing_tokens:
        return _status(
            INCOMPATIBLE,
            "launcher_interface_unsupported",
            f"{name} help output is missing audited interface tokens.",
            name=name,
            missing_help_tokens=missing_tokens,
            execution=run,
        )
    return _status(
        OPERATIONAL,
        "launcher_interface_operational",
        f"{name} help output matches the audited interface.",
        name=name,
        command=list(command),
        missing_help_tokens=[],
    )


def _interface_entries(skill_name: str) -> list[tuple[str, Mapping[str, Any]]]:
    return [
        (name, contract)
        for name, contract in INTERFACES.items()
        if contract.get("skill") == skill_name
    ]


def _aggregate_component(
    skill_name: str,
    *,
    selected: Mapping[str, Any] | None,
    provenance: Mapping[str, Any] | None,
    checks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    statuses = [str(check.get("status", SKIPPED)) for check in checks]
    if provenance is not None:
        statuses.insert(0, str(provenance.get("status", SKIPPED)))
    if INCOMPATIBLE in statuses:
        result_status = INCOMPATIBLE
        reason = "component_incompatible"
        message = f"{skill_name} is installed but does not match the audited interface."
    elif UNAVAILABLE in statuses:
        result_status = UNAVAILABLE
        reason = "component_unavailable"
        message = f"{skill_name} or one of its required runtimes is unavailable."
    elif (
        provenance is not None
        and provenance.get("status") == OPERATIONAL
        and checks
        and all(check.get("status") == OPERATIONAL for check in checks)
    ):
        result_status = OPERATIONAL
        reason = "component_operational"
        message = f"{skill_name} matches the audited v{AUDITED_VERSION} interface."
    else:
        result_status = SKIPPED
        reason = "component_checks_skipped"
        message = f"{skill_name} could not be fully probed."
    return _status(
        result_status,
        reason,
        message,
        selected=dict(selected) if selected else None,
        provenance=dict(provenance) if provenance else None,
        checks=[dict(check) for check in checks],
        interfaces={
            name: dict(contract) for name, contract in _interface_entries(skill_name)
        },
    )


def probe_python_skill(
    skill_name: str,
    selected: Mapping[str, Any] | None,
    *,
    repo: Path,
    home: Path,
    python_runtime: Mapping[str, Any],
    timeout: int,
    expected_hashes: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    if selected is None:
        return _status(
            UNAVAILABLE,
            "skill_not_found",
            f"{skill_name} was not discovered in project, local, or global skill paths.",
            selected=None,
            provenance=None,
            checks=[],
            interfaces={
                name: dict(contract)
                for name, contract in _interface_entries(skill_name)
            },
        )
    skill_path = Path(str(selected["path"])).resolve()
    provenance = probe_provenance(
        repo,
        skill_name,
        skill_path,
        home=home,
        expected_hashes=expected_hashes,
    )
    if provenance["status"] != OPERATIONAL:
        checks = [
            _skipped_check(
                name,
                "Launcher and import probes require compatible audited skill provenance.",
            )
            for name, _ in _interface_entries(skill_name)
        ]
        checks.append(
            _skipped_check(
                "python_imports",
                "Import probes require compatible audited skill provenance.",
            )
        )
        return _aggregate_component(
            skill_name,
            selected=selected,
            provenance=provenance,
            checks=checks,
        )

    if python_runtime["status"] != OPERATIONAL:
        checks = [
            _status(
                str(python_runtime["status"]),
                str(python_runtime["reason_code"]),
                str(python_runtime["message"]),
                name="python_runtime",
            )
        ]
        checks.extend(
            _skipped_check(
                name,
                "Launcher help requires an operational Python 3.12+ interpreter.",
            )
            for name, _ in _interface_entries(skill_name)
        )
        checks.append(
            _skipped_check(
                "python_imports",
                "Import probes require an operational Python 3.12+ interpreter.",
            )
        )
        return _aggregate_component(
            skill_name,
            selected=selected,
            provenance=provenance,
            checks=checks,
        )

    import_contract = PYTHON_IMPORTS[skill_name]
    import_paths = [skill_path / relative for relative in import_contract["paths"]]
    import_probe = probe_python_imports(
        python_runtime,
        modules=import_contract["modules"],
        paths=import_paths,
        timeout=timeout,
    )
    checks: list[Mapping[str, Any]] = [
        _status(
            str(import_probe["status"]),
            str(import_probe["reason_code"]),
            str(import_probe["message"]),
            name="python_imports",
            details=dict(import_probe),
        )
    ]
    python_executable = str(python_runtime["executable"])
    for interface_name, contract in _interface_entries(skill_name):
        launcher = skill_path / str(contract["launcher"])
        if not launcher.exists():
            checks.append(
                _status(
                    INCOMPATIBLE,
                    "launcher_missing",
                    f"Audited launcher is missing: {launcher}",
                    name=interface_name,
                    path=str(launcher),
                )
            )
            continue
        checks.append(
            probe_help(
                [python_executable, str(launcher), "--help"],
                cwd=repo,
                timeout=timeout,
                required_tokens=list(contract["required_help_tokens"]),
                name=interface_name,
            )
        )
    return _aggregate_component(
        skill_name,
        selected=selected,
        provenance=provenance,
        checks=checks,
    )


def probe_cad_viewer(
    selected: Mapping[str, Any] | None,
    *,
    repo: Path,
    home: Path,
    npm_command: str,
    timeout: int,
    expected_hashes: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    skill_name = "cad-viewer"
    if selected is None:
        return _status(
            UNAVAILABLE,
            "skill_not_found",
            "cad-viewer was not discovered in project, local, or global skill paths.",
            selected=None,
            provenance=None,
            checks=[],
            interfaces={
                name: dict(contract)
                for name, contract in _interface_entries(skill_name)
            },
        )
    skill_path = Path(str(selected["path"])).resolve()
    provenance = probe_provenance(
        repo,
        skill_name,
        skill_path,
        home=home,
        expected_hashes=expected_hashes,
    )
    interface_name, contract = _interface_entries(skill_name)[0]
    if provenance["status"] != OPERATIONAL:
        return _aggregate_component(
            skill_name,
            selected=selected,
            provenance=provenance,
            checks=[
                _skipped_check(
                    interface_name,
                    "Viewer launcher probing requires compatible audited skill provenance.",
                )
            ],
        )

    viewer_root = skill_path / "scripts" / "viewer"
    package_path = viewer_root / "package.json"
    if not package_path.is_file():
        checks = [
            _status(
                INCOMPATIBLE,
                "viewer_package_missing",
                f"cad-viewer package.json is missing: {package_path}",
                name=interface_name,
            )
        ]
        return _aggregate_component(
            skill_name,
            selected=selected,
            provenance=provenance,
            checks=checks,
        )
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        checks = [
            _status(
                INCOMPATIBLE,
                "viewer_package_invalid",
                f"cad-viewer package.json could not be read: {exc}",
                name=interface_name,
            )
        ]
        return _aggregate_component(
            skill_name,
            selected=selected,
            provenance=provenance,
            checks=checks,
        )
    scripts = package.get("scripts") if isinstance(package, Mapping) else None
    available_scripts = (
        sorted(str(name) for name in scripts)
        if isinstance(scripts, Mapping)
        else []
    )
    if not isinstance(scripts, Mapping) or "agent:start" not in scripts:
        checks = [
            _status(
                INCOMPATIBLE,
                "audited_v0_3_9_agent_start_missing",
                (
                    "Audited text-to-CAD v0.3.9 documents `agent:start`, but the "
                    "bundled cad-viewer package does not define that script."
                ),
                name=interface_name,
                package_json=str(package_path),
                available_scripts=available_scripts,
            )
        ]
        return _aggregate_component(
            skill_name,
            selected=selected,
            provenance=provenance,
            checks=checks,
        )

    npm_executable = _resolve_executable(npm_command)
    if npm_executable is None:
        checks = [
            _status(
                UNAVAILABLE,
                "npm_not_found",
                f"npm command {npm_command!r} was not found.",
                name=interface_name,
            )
        ]
        return _aggregate_component(
            skill_name,
            selected=selected,
            provenance=provenance,
            checks=checks,
        )
    checks = [
        probe_help(
            [
                npm_executable,
                "--prefix",
                str(viewer_root),
                "run",
                "agent:start",
                "--",
                "--help",
            ],
            cwd=repo,
            timeout=timeout,
            required_tokens=list(contract["required_help_tokens"]),
            name=interface_name,
        )
    ]
    return _aggregate_component(
        skill_name,
        selected=selected,
        provenance=provenance,
        checks=checks,
    )


def _viewer_fallback(components: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    viewer_status = components["cad-viewer"]["status"]
    if viewer_status == OPERATIONAL:
        return _status(
            SKIPPED,
            "viewer_operational",
            "The viewer is operational; deterministic inspection and snapshots remain required.",
            required=False,
            commands=[
                INTERFACES["cad.inspect"]["command"],
                INTERFACES["cad.snapshot"]["command"],
            ],
        )
    cad_status = components["cad"]["status"]
    if cad_status == OPERATIONAL:
        return _status(
            OPERATIONAL,
            "inspect_snapshot_fallback_operational",
            (
                "cad-viewer is not operational. Use deterministic inspect facts, "
                "planes, positioning, measurements, alignment, frame/diff checks, "
                "and the mandatory STEP snapshot."
            ),
            required=True,
            commands=[
                INTERFACES["cad.inspect"]["command"],
                INTERFACES["cad.snapshot"]["command"],
            ],
        )
    return _status(
        UNAVAILABLE,
        "inspect_snapshot_fallback_unavailable",
        (
            "cad-viewer is not operational and the CAD inspect/snapshot capability "
            "is also unavailable or incompatible."
        ),
        required=True,
        commands=[
            INTERFACES["cad.inspect"]["command"],
            INTERFACES["cad.snapshot"]["command"],
        ],
    )


def _overall_status(components: Mapping[str, Mapping[str, Any]]) -> str:
    statuses = [str(component["status"]) for component in components.values()]
    if INCOMPATIBLE in statuses:
        return INCOMPATIBLE
    if UNAVAILABLE in statuses:
        return UNAVAILABLE
    if OPERATIONAL in statuses:
        return OPERATIONAL
    return SKIPPED


def probe_text_to_cad(
    repo: Path,
    *,
    python_command: str = sys.executable,
    npm_command: str = "npm",
    timeout: int = 10,
    home: Path | None = None,
    discovery_roots: Sequence[tuple[str, Path]] | None = None,
    skills_command: str | None = None,
    use_skills_cli: bool = True,
    expected_hashes: Mapping[str, Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    target_repo = repo.expanduser().resolve()
    home_path = (home or Path.home()).expanduser().resolve()
    hashes = EXPECTED_SKILL_HASHES if expected_hashes is None else expected_hashes
    discovery = discover_skills(
        target_repo,
        home=home_path,
        timeout=timeout,
        roots=discovery_roots,
        skills_command=skills_command,
        use_skills_cli=use_skills_cli,
    )
    python_runtime = probe_python_runtime(python_command, timeout=timeout)
    selected = discovery["selected"]
    components: dict[str, dict[str, Any]] = {}
    for name in ("cad", "step-parts", "urdf", "srdf", "sdf"):
        components[name] = probe_python_skill(
            name,
            selected[name],
            repo=target_repo,
            home=home_path,
            python_runtime=python_runtime,
            timeout=timeout,
            expected_hashes=hashes,
        )
    components["cad-viewer"] = probe_cad_viewer(
        selected["cad-viewer"],
        repo=target_repo,
        home=home_path,
        npm_command=npm_command,
        timeout=timeout,
        expected_hashes=hashes,
    )
    ordered_components = {name: components[name] for name in SKILL_NAMES}
    overall = _overall_status(ordered_components)
    counts = {
        status: sum(
            1 for component in ordered_components.values() if component["status"] == status
        )
        for status in STATUSES
    }
    return {
        "status": overall,
        "reason_code": f"probe_{overall}",
        "message": (
            f"text-to-CAD v{AUDITED_VERSION} probe completed: "
            + ", ".join(f"{status}={counts[status]}" for status in STATUSES)
            + "."
        ),
        "repo": str(target_repo),
        "audited_contract": audited_contract(),
        "discovery": discovery,
        "python_runtime": python_runtime,
        "components": ordered_components,
        "viewer_fallback": _viewer_fallback(ordered_components),
        "summary": counts,
        "request_gate": None,
        "safety": {
            "read_only": True,
            "network_requests_executed": False,
            "generation_commands_executed": [],
            "physical_actions_executed": [],
        },
    }


def apply_required_feature_gate(
    report: Mapping[str, Any],
    required_features: Sequence[str],
) -> dict[str, Any]:
    requested = list(dict.fromkeys(required_features))
    components = report.get("components")
    blocked: list[dict[str, str]] = []
    if isinstance(components, Mapping):
        for feature in requested:
            component = components.get(feature)
            if not isinstance(component, Mapping) or component.get("status") != OPERATIONAL:
                blocked.append(
                    {
                        "feature": feature,
                        "detected_status": (
                            str(component.get("status"))
                            if isinstance(component, Mapping)
                            else UNAVAILABLE
                        ),
                        "reason_code": (
                            str(component.get("reason_code"))
                            if isinstance(component, Mapping)
                            else "feature_not_reported"
                        ),
                    }
                )
    if blocked:
        return _status(
            INCOMPATIBLE,
            "required_feature_not_operational",
            "One or more explicitly required text-to-CAD features are not operational.",
            compatible=False,
            required_features=requested,
            blocked=blocked,
        )
    return _status(
        OPERATIONAL,
        "required_features_operational",
        "Every explicitly required text-to-CAD feature is operational.",
        compatible=True,
        required_features=requested,
        blocked=[],
    )


def _parse_root(value: str) -> tuple[str, Path]:
    if "=" not in value:
        return "local", Path(value)
    scope, path_text = value.split("=", 1)
    if scope not in SCOPE_PRIORITY:
        raise argparse.ArgumentTypeError(
            "--skill-root scope must be project, local, global, or unknown"
        )
    if not path_text:
        raise argparse.ArgumentTypeError("--skill-root path must not be empty")
    return scope, Path(path_text)


def emit(report: Mapping[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"{str(report.get('status', INCOMPATIBLE)).upper()}: {report.get('message')}")
    components = report.get("components")
    if isinstance(components, Mapping):
        for name in SKILL_NAMES:
            component = components.get(name, {})
            print(
                f"- {name}: {str(component.get('status', UNAVAILABLE)).upper()} "
                f"({component.get('reason_code', 'not_reported')})"
            )
    fallback = report.get("viewer_fallback")
    if isinstance(fallback, Mapping) and fallback.get("required"):
        print(f"Viewer fallback: {fallback.get('message')}")
    gate = report.get("request_gate")
    if isinstance(gate, Mapping):
        print(
            f"Required feature gate: {str(gate.get('status', INCOMPATIBLE)).upper()} "
            f"({gate.get('reason_code')})"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only discovery and compatibility probe for the audited "
            "earthtojake/text-to-cad v0.3.9 skill interfaces."
        )
    )
    parser.add_argument("repo", nargs="?", default=".", help="target repository")
    parser.add_argument(
        "--python-command",
        default=sys.executable,
        help=(
            "Python interpreter used only for version, import, and launcher help probes "
            "(default: the interpreter running this probe)"
        ),
    )
    parser.add_argument(
        "--npm-command",
        default="npm",
        help="npm executable used only for the cad-viewer launcher help probe",
    )
    parser.add_argument(
        "--skills-command",
        help=(
            "already-installed skills CLI executable; default discovery tries `skills`, "
            "then `npx --no-install skills` without package installation"
        ),
    )
    parser.add_argument(
        "--skip-skills-cli",
        action="store_true",
        help="use filesystem discovery only",
    )
    parser.add_argument(
        "--skill-root",
        action="append",
        type=_parse_root,
        default=[],
        metavar="[SCOPE=]PATH",
        help="override default skill roots; repeat for multiple scopes",
    )
    parser.add_argument(
        "--require-feature",
        action="append",
        choices=SKILL_NAMES,
        default=[],
        help="fail closed unless this feature is operational; repeat as needed",
    )
    parser.add_argument("--timeout", type=int, default=10, help="per-command timeout seconds")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    repo = Path(args.repo)
    if not repo.expanduser().resolve().is_dir():
        parser.error(f"target repository does not exist: {repo}")
    roots = args.skill_root or None
    report = probe_text_to_cad(
        repo,
        python_command=args.python_command,
        npm_command=args.npm_command,
        timeout=args.timeout,
        discovery_roots=roots,
        skills_command=args.skills_command,
        use_skills_cli=not args.skip_skills_cli,
    )
    if args.require_feature:
        report["request_gate"] = apply_required_feature_gate(
            report, args.require_feature
        )
    emit(report, as_json=args.json)
    gate = report.get("request_gate")
    return 1 if isinstance(gate, Mapping) and gate.get("status") == INCOMPATIBLE else 0


if __name__ == "__main__":
    raise SystemExit(main())
