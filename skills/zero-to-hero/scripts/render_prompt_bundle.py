#!/usr/bin/env python3
"""Render prompt bundles from the canonical executable contract graph."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from zero_to_hero_contract import (  # noqa: E402
    ContractError,
    load_graph,
    prompt_by_id,
    render_prompt,
    skill_root_from,
)


def render(
    skill: Path,
    group: str,
    target_repo: str | None,
) -> tuple[str, dict]:
    graph = load_graph(skill)
    groups = graph["prompt_groups"]
    if group not in groups:
        raise ContractError(f"unknown group {group!r}; choose one of {sorted(groups)}")
    by_id = prompt_by_id(graph)
    prompt_ids = groups[group]
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "# zero-to-hero prompt bundle",
        "",
        f"- generated_at: {generated_at}",
        f"- group: {group}",
        f"- source: `{skill / 'references/contract-graph.yaml'}`",
    ]
    target = str(Path(target_repo).resolve()) if target_repo else None
    if target:
        lines.append(f"- target_repo: `{target}`")
    lines.extend(
        [
            "",
            "Run the prompts in the listed order. `one_shot` is an alternative group and is never appended to the canonical sequence.",
            "",
        ]
    )
    names: list[str] = []
    for index, prompt_id in enumerate(prompt_ids, start=1):
        contract = by_id[prompt_id]
        names.append(contract["prompt_file"])
        lines.extend(
            [
                "---",
                "",
                f"## {index}. {contract['title']}",
                "",
                f"Path: `prompts/{contract['prompt_file']}`",
                "",
            ]
        )
        if target:
            lines.extend([f"Target repository: `{target}`", ""])
        lines.append(
            render_prompt(
                contract,
                global_forbidden_write_paths=graph["global_forbidden_write_paths"],
                global_forbidden_write_exceptions=graph[
                    "global_forbidden_write_exceptions"
                ],
            ).rstrip()
        )
        lines.append("")
    manifest = {
        "generated_at": generated_at,
        "group": group,
        "prompt_ids": prompt_ids,
        "prompts": names,
        "target_repo": target,
        "source": "references/contract-graph.yaml",
    }
    return "\n".join(lines).rstrip() + "\n", manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1]),
        help="skill root or repo containing .agents/skills/zero-to-hero",
    )
    parser.add_argument("--group", default="canonical")
    parser.add_argument("--target-repo")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        skill = skill_root_from(args.skill)
        bundle, manifest = render(skill, args.group, args.target_repo)
    except ContractError as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 1
    if args.write or args.out:
        if args.out:
            out = Path(args.out).resolve()
        elif args.target_repo:
            out = (
                Path(args.target_repo).resolve()
                / ".codex/reports/zero-to-hero/prompt-bundle.md"
            )
        else:
            print("--write requires --target-repo or --out", file=sys.stderr)
            return 2
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(bundle, encoding="utf-8")
        manifest_path = out.with_suffix(".manifest.json")
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": "written",
                    "bundle": str(out),
                    "manifest": str(manifest_path),
                    "prompt_count": len(manifest["prompts"]),
                },
                indent=2,
            )
        )
    else:
        print(bundle, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
