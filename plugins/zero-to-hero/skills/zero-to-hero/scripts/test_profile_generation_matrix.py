#!/usr/bin/env python3
"""Generate and audit every declared output profile in temporary repositories."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import apply_zero_to_hero_templates as generator  # noqa: E402
import target_repo_audit as audit  # noqa: E402
from zero_to_hero_contract import load_graph, load_profiles, selected_artifacts  # noqa: E402

SKILL = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed: {result.stdout}\n{result.stderr}"
        )


def initialized_repo(root: Path) -> Path:
    repo = root / "target"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "checkout", "-q", "-b", "codex/profile-generation-test")
    (repo / "seed.txt").write_text("profile generation fixture\n", encoding="utf-8")
    git(repo, "add", "seed.txt")
    git(repo, "commit", "-q", "-m", "fixture")
    return repo


class ProfileGenerationMatrixTests(unittest.TestCase):
    def test_every_profile_generates_exact_required_artifacts_and_audits(self) -> None:
        graph = load_graph(SKILL)
        profiles = load_profiles(SKILL)
        for profile_id in sorted(profiles):
            with self.subTest(profile=profile_id):
                with tempfile.TemporaryDirectory(prefix=f"z2h-{profile_id}-") as temp:
                    repo = initialized_repo(Path(temp))
                    manifest = generator.execute_generation(
                        skill=SKILL,
                        repo=repo,
                        explicit_profiles=(profile_id,),
                        dry_run=False,
                    )
                    selected = manifest["selected_profiles"]
                    artifacts = selected_artifacts(graph, profiles, selected)
                    required = {
                        item["path"]
                        for item in artifacts["required"]
                        if item["path"] != generator.CANONICAL_MANIFEST.as_posix()
                    }
                    self.assertTrue(
                        all((repo / path).is_file() for path in required),
                        f"{profile_id} omitted a required artifact",
                    )
                    self.assertTrue(
                        all(not (repo / path).exists() for path in artifacts["forbidden"]),
                        f"{profile_id} emitted a forbidden artifact",
                    )
                    on_disk = json.loads(
                        (repo / generator.CANONICAL_MANIFEST).read_text(encoding="utf-8")
                    )
                    generator.validate_manifest(on_disk)
                    handoff_check = subprocess.run(
                        [
                            sys.executable,
                            str(repo / generator.HANDOFF_CHECK),
                            str(repo),
                        ],
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(
                        handoff_check.returncode,
                        0,
                        handoff_check.stderr or handoff_check.stdout,
                    )
                    report = audit.audit_target(
                        repo=repo,
                        skill=SKILL,
                        explicit_profiles=(profile_id,),
                    )
                    self.assertTrue(report["ready"], report["failures"])

    def test_robotics_and_mechanical_generation_proves_cad_contract(self) -> None:
        for profile_id in ("mechanical-product", "robotics-product"):
            with self.subTest(profile=profile_id):
                with tempfile.TemporaryDirectory(prefix=f"z2h-cad-{profile_id}-") as temp:
                    repo = initialized_repo(Path(temp))
                    generator.execute_generation(
                        skill=SKILL,
                        repo=repo,
                        explicit_profiles=(profile_id,),
                        dry_run=False,
                    )
                    adapter = (repo / "docs/mechanical/cad-adapter.md").read_text(
                        encoding="utf-8"
                    )
                    mechanical = "\n".join(
                        [
                            adapter,
                            (repo / "docs/mechanical/requirements.md").read_text(
                                encoding="utf-8"
                            ),
                            (
                                repo / "docs/mechanical/interfaces-and-datums.md"
                            ).read_text(encoding="utf-8"),
                            (
                                repo / "docs/mechanical/dimensions-and-tolerances.yaml"
                            ).read_text(encoding="utf-8"),
                        ]
                    ).lower()
                    for token in (
                        "earthtojake/text-to-cad",
                        "$step-parts",
                        "build123d",
                        "step",
                        "snapshot",
                        "$cad-viewer",
                        "fallback",
                        "dimension",
                        "tolerance",
                        "datum",
                        "coordinate frame",
                        "human engineering review",
                        "physical",
                        "authorization",
                    ):
                        self.assertIn(token, mechanical)
                    generated_geometry = [
                        path
                        for suffix in ("*.step", "*.stp", "*.stl", "*.3mf", "*.glb")
                        for path in repo.rglob(suffix)
                    ]
                    self.assertEqual(generated_geometry, [])

                    if profile_id == "robotics-product":
                        robotics = "\n".join(
                            path.read_text(encoding="utf-8")
                            for path in sorted((repo / "docs/robotics").glob("*.md"))
                        ).lower()
                        for token in (
                            "urdf",
                            "srdf",
                            "sdf",
                            "kinematic",
                            "inertial",
                            "visual",
                            "collision",
                            "simulation",
                            "bring-up",
                            "telemetry",
                            "failure",
                        ):
                            self.assertIn(token, robotics)

    def test_web_profile_does_not_receive_hardware_scaffolding(self) -> None:
        with tempfile.TemporaryDirectory(prefix="z2h-negative-web-") as temp:
            repo = initialized_repo(Path(temp))
            generator.execute_generation(
                skill=SKILL,
                repo=repo,
                explicit_profiles=("web-app",),
                dry_run=False,
            )
            for path in (
                "docs/firmware",
                "docs/mechanical",
                "docs/pcb",
                "docs/robotics",
            ):
                self.assertFalse((repo / path).exists(), path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
