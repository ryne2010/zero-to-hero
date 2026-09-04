#!/usr/bin/env python3
"""Hermetic behavior checks for the text-to-CAD compatibility probe."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import sys
from pathlib import Path
from typing import Any, Mapping

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import text_to_cad_probe as probe  # noqa: E402


class ProbeTestFailure(RuntimeError):
    pass


def _assert(
    checks: list[dict[str, Any]],
    condition: bool,
    name: str,
    detail: Any = None,
) -> None:
    checks.append({"check": name, "ok": bool(condition), "detail": detail})
    if not condition:
        raise ProbeTestFailure(f"{name}: {detail}")


def _write_python_command(path: Path, content: str) -> Path:
    """Create a directly invokable Python-backed fake on POSIX and Windows."""

    path.parent.mkdir(parents=True, exist_ok=True)
    script = path.with_name(path.name + ".py")
    script.write_text(content, encoding="utf-8")
    if os.name == "nt":
        command = path.with_name(path.name + ".cmd")
        command.write_text(
            f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n',
            encoding="utf-8",
        )
    else:
        command = path
        command.write_text(content, encoding="utf-8")
        command.chmod(0o755)
    return command


def _fake_python(
    path: Path,
    version: tuple[int, int, int],
    *,
    missing_import: bool = False,
) -> Path:
    help_text = " ".join(
        sorted(
            {
                token
                for contract in probe.INTERFACES.values()
                if contract["skill"] != "cad-viewer"
                for token in contract["required_help_tokens"]
            }
        )
    )
    import_payload = (
        '{"probe":"text-to-cad-python-imports","loaded":[],'
        '"missing":[{"module":"build123d",'
        '"error":"ImportError: synthetic missing dependency"}]}'
        if missing_import
        else '{"probe":"text-to-cad-python-imports","loaded":[],"missing":[]}'
    )
    runtime_payload = json.dumps(
        {
            "probe": "text-to-cad-python-runtime",
            "version": list(version),
            "executable": "synthetic-python",
        },
        separators=(",", ":"),
    )
    content = f"""#!/usr/bin/env python3
import sys

if sys.argv[1:2] == ["-c"]:
    if "\\n" in sys.argv[2] or "\\r" in sys.argv[2]:
        raise SystemExit("multiline -c payload is not safe through a batch proxy")
    if "text-to-cad-python-runtime" in sys.argv[2]:
        print({runtime_payload!r})
    else:
        print({import_payload!r})
else:
    print({help_text!r})
"""
    return _write_python_command(path, content)


def _fake_npm(path: Path) -> Path:
    return _write_python_command(
        path,
        "#!/usr/bin/env python3\nprint('viewer options: --host HOST --dir ROOT')\n",
    )


def _write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_skill(root: Path, name: str, *, viewer_agent_start: bool = False) -> Path:
    skill = root / name
    _write_file(
        skill / "SKILL.md",
        f"---\nname: {name}\ndescription: Synthetic {name} compatibility surface.\n---\n",
    )
    _write_file(skill / "LICENSE", "Synthetic test material.\n")
    if name == "cad":
        _write_file(skill / "scripts" / "step" / "__main__.py")
        _write_file(skill / "scripts" / "inspect" / "__main__.py")
        _write_file(skill / "scripts" / "snapshot" / "__main__.py")
        _write_file(
            skill / "scripts" / "packages" / "cadpy" / "src" / "cadpy" / "__init__.py"
        )
    elif name == "step-parts":
        _write_file(skill / "scripts" / "download_step_part.py")
    elif name in {"urdf", "srdf", "sdf"}:
        _write_file(skill / "scripts" / name / "__main__.py")
        _write_file(
            skill
            / "scripts"
            / "packages"
            / "cadpy_metadata"
            / "src"
            / "cadpy_metadata"
            / "__init__.py"
        )
    elif name == "cad-viewer":
        scripts = {"start": "node backend/server.mjs"}
        if viewer_agent_start:
            scripts["agent:start"] = "node backend/server.mjs"
        _write_file(
            skill / "scripts" / "viewer" / "package.json",
            json.dumps({"name": "synthetic-viewer", "scripts": scripts}, indent=2) + "\n",
        )
    return skill


def _create_all_skills(root: Path, *, viewer_agent_start: bool = False) -> None:
    for name in probe.SKILL_NAMES:
        _create_skill(root, name, viewer_agent_start=viewer_agent_start)


def _expected_hashes(
    root: Path,
    *,
    cli_hashes: bool = True,
) -> dict[str, dict[str, str]]:
    expected: dict[str, dict[str, str]] = {}
    for name in probe.SKILL_NAMES:
        skill = root / name
        if not skill.is_dir():
            continue
        record = {"portable_tree_sha256": probe.compute_portable_tree_hash(skill)}
        if cli_hashes:
            record["skills_cli"] = f"synthetic-cli-hash-{name}"
        expected[name] = record
    return expected


def _write_lock(
    path: Path,
    root: Path,
    *,
    ref_overrides: Mapping[str, str] | None = None,
    hash_overrides: Mapping[str, str] | None = None,
) -> None:
    expected = _expected_hashes(root)
    skills: dict[str, dict[str, str]] = {}
    for name in expected:
        skills[name] = {
            "source": probe.AUDITED_SOURCE,
            "ref": (ref_overrides or {}).get(name, probe.AUDITED_VERSION),
            "sourceType": "github",
            "skillPath": f"skills/{name}/SKILL.md",
            "computedHash": (hash_overrides or {}).get(
                name, expected[name]["skills_cli"]
            ),
        }
    _write_file(path, json.dumps({"version": 1, "skills": skills}, indent=2) + "\n")


def _project_report(
    repo: Path,
    skill_root: Path,
    home: Path,
    python_path: Path,
    npm_path: Path,
    expected: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    return probe.probe_text_to_cad(
        repo,
        python_command=str(python_path),
        npm_command=str(npm_path),
        timeout=3,
        home=home,
        discovery_roots=[("project", skill_root)],
        use_skills_cli=False,
        expected_hashes=expected,
    )


def run_tests() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="zero-to-hero-text-to-cad-") as temp:
        root = Path(temp)
        bin_dir = root / "bin"
        python_312 = _fake_python(bin_dir / "python-3.12", (3, 12, 8))
        python_311 = _fake_python(bin_dir / "python-3.11", (3, 11, 9))
        python_missing_import = _fake_python(
            bin_dir / "python-missing-import",
            (3, 12, 8),
            missing_import=True,
        )
        npm = _fake_npm(bin_dir / "npm")
        _assert(
            checks,
            (bin_dir / "python-3.12.py").is_file()
            and (bin_dir / "python-3.11.py").is_file(),
            "python:dotted-fake-names-remain-distinct",
        )

        absent_repo = root / "absent-repo"
        absent_repo.mkdir()
        absent = probe.probe_text_to_cad(
            absent_repo,
            python_command=str(python_312),
            npm_command=str(npm),
            timeout=3,
            home=root / "absent-home",
            discovery_roots=[("project", absent_repo / ".agents" / "skills")],
            use_skills_cli=False,
        )
        _assert(
            checks,
            absent["status"] == probe.UNAVAILABLE,
            "absent:overall-unavailable",
            absent["status"],
        )
        _assert(
            checks,
            all(
                component["status"] == probe.UNAVAILABLE
                for component in absent["components"].values()
            ),
            "absent:components-unavailable",
            absent["summary"],
        )
        _assert(
            checks,
            probe.apply_required_feature_gate(absent, ["cad"])["status"]
            == probe.INCOMPATIBLE,
            "absent:required-feature-fails-closed",
        )

        project_repo = root / "project-repo"
        project_repo.mkdir()
        project_skills = project_repo / ".agents" / "skills"
        _create_all_skills(project_skills)
        project_expected = _expected_hashes(project_skills)
        _write_lock(project_repo / "skills-lock.json", project_skills)
        project = _project_report(
            project_repo,
            project_skills,
            root / "project-home",
            python_312,
            npm,
            project_expected,
        )
        for name in ("cad", "step-parts", "urdf", "srdf", "sdf"):
            _assert(
                checks,
                project["components"][name]["status"] == probe.OPERATIONAL,
                f"project:{name}-operational",
                project["components"][name],
            )
        _assert(
            checks,
            project["components"]["cad-viewer"]["status"] == probe.INCOMPATIBLE,
            "project:viewer-defect-visible",
            project["components"]["cad-viewer"],
        )
        viewer_checks = project["components"]["cad-viewer"]["checks"]
        _assert(
            checks,
            any(
                check.get("reason_code")
                == "audited_v0_3_9_agent_start_missing"
                for check in viewer_checks
            ),
            "project:viewer-defect-reason",
            viewer_checks,
        )
        _assert(
            checks,
            project["viewer_fallback"]["status"] == probe.OPERATIONAL
            and project["viewer_fallback"]["required"] is True,
            "project:inspect-snapshot-fallback",
            project["viewer_fallback"],
        )
        _assert(
            checks,
            probe.apply_required_feature_gate(project, ["cad"])["status"]
            == probe.OPERATIONAL,
            "project:operational-feature-gate",
        )
        _assert(
            checks,
            probe.apply_required_feature_gate(project, ["cad-viewer"])["status"]
            == probe.INCOMPATIBLE,
            "project:viewer-gate-fails-closed",
        )
        missing_import = _project_report(
            project_repo,
            project_skills,
            root / "import-home",
            python_missing_import,
            npm,
            project_expected,
        )
        _assert(
            checks,
            missing_import["components"]["cad"]["status"] == probe.UNAVAILABLE,
            "project:missing-import-unavailable",
            missing_import["components"]["cad"],
        )

        global_repo = root / "global-repo"
        global_repo.mkdir()
        global_home = root / "global-home"
        global_skills = global_home / ".codex" / "skills"
        _create_skill(global_skills, "step-parts")
        global_expected = _expected_hashes(global_skills)
        _write_lock(
            global_repo / "skills-lock.json",
            global_skills,
            ref_overrides={"step-parts": "0.4.0"},
        )
        _write_lock(global_home / ".codex" / "skills-lock.json", global_skills)
        global_report = probe.probe_text_to_cad(
            global_repo,
            python_command=str(python_312),
            npm_command=str(npm),
            timeout=3,
            home=global_home,
            discovery_roots=[("global", global_skills)],
            use_skills_cli=False,
            expected_hashes=global_expected,
        )
        _assert(
            checks,
            global_report["components"]["step-parts"]["status"] == probe.OPERATIONAL,
            "global:step-parts-operational",
            global_report["components"]["step-parts"],
        )
        _assert(
            checks,
            global_report["components"]["step-parts"]["selected"]["scope"] == "global",
            "global:scope-recorded",
            global_report["components"]["step-parts"]["selected"],
        )
        unverified = probe.probe_text_to_cad(
            global_repo,
            python_command=str(python_312),
            npm_command=str(npm),
            timeout=3,
            home=global_home,
            discovery_roots=[("global", global_skills)],
            use_skills_cli=False,
            expected_hashes={},
        )
        _assert(
            checks,
            unverified["components"]["step-parts"]["status"] == probe.SKIPPED,
            "global:unverified-content-skipped",
            unverified["components"]["step-parts"],
        )

        version_repo = root / "version-repo"
        version_repo.mkdir()
        version_skills = version_repo / ".agents" / "skills"
        _create_skill(version_skills, "cad")
        version_expected = _expected_hashes(version_skills)
        _write_lock(
            version_repo / "skills-lock.json",
            version_skills,
            ref_overrides={"cad": "0.4.0"},
        )
        wrong_ref = _project_report(
            version_repo,
            version_skills,
            root / "version-home",
            python_312,
            npm,
            version_expected,
        )
        _assert(
            checks,
            wrong_ref["components"]["cad"]["status"] == probe.INCOMPATIBLE,
            "provenance:wrong-ref-incompatible",
            wrong_ref["components"]["cad"],
        )

        _write_lock(
            version_repo / "skills-lock.json",
            version_skills,
            hash_overrides={"cad": "not-the-audited-hash"},
        )
        wrong_hash = _project_report(
            version_repo,
            version_skills,
            root / "hash-home",
            python_312,
            npm,
            version_expected,
        )
        _assert(
            checks,
            wrong_hash["components"]["cad"]["status"] == probe.INCOMPATIBLE,
            "provenance:wrong-hash-incompatible",
            wrong_hash["components"]["cad"],
        )

        _write_lock(version_repo / "skills-lock.json", version_skills)
        old_python = _project_report(
            version_repo,
            version_skills,
            root / "python-home",
            python_311,
            npm,
            version_expected,
        )
        _assert(
            checks,
            old_python["python_runtime"]["status"] == probe.INCOMPATIBLE,
            "python:3.11-incompatible",
            old_python["python_runtime"],
        )
        _assert(
            checks,
            old_python["components"]["cad"]["status"] == probe.INCOMPATIBLE,
            "python:required-cad-fails-closed",
            old_python["components"]["cad"],
        )

        repaired_repo = root / "viewer-interface-repo"
        repaired_repo.mkdir()
        repaired_skills = repaired_repo / ".agents" / "skills"
        _create_skill(repaired_skills, "cad-viewer", viewer_agent_start=True)
        repaired_expected = _expected_hashes(repaired_skills)
        _write_lock(repaired_repo / "skills-lock.json", repaired_skills)
        repaired = _project_report(
            repaired_repo,
            repaired_skills,
            root / "viewer-home",
            python_312,
            npm,
            repaired_expected,
        )
        _assert(
            checks,
            repaired["components"]["cad-viewer"]["status"] == probe.OPERATIONAL,
            "viewer:launcher-help-probed",
            repaired["components"]["cad-viewer"],
        )

    return {
        "status": "PASS",
        "message": "Hermetic text-to-CAD compatibility probe checks passed.",
        "checks": checks,
        "temporary_artifacts_retained": False,
        "network_requests_executed": False,
        "physical_actions_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    try:
        report = run_tests()
    except Exception as exc:
        report = {
            "status": "FAIL",
            "message": f"Hermetic text-to-CAD probe checks failed: {type(exc).__name__}: {exc}",
            "checks": [],
            "temporary_artifacts_retained": False,
            "network_requests_executed": False,
            "physical_actions_executed": False,
        }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['status']}: {report['message']}")
        if report.get("checks"):
            print(f"Checks: {sum(1 for check in report['checks'] if check.get('ok'))}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
