#!/usr/bin/env python3
"""Generate or verify prompt and phase views derived from contract-graph.yaml."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from zero_to_hero_contract import (  # noqa: E402
    ContractError,
    load_graph,
    rendered_contract_views,
    skill_root_from,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1]),
        help="zero-to-hero skill root",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write all generated views; default is byte-for-byte verification",
    )
    args = parser.parse_args()
    try:
        skill = skill_root_from(args.skill)
        graph = load_graph(skill)
        expected = rendered_contract_views(graph)
    except ContractError as exc:
        print(f"contract error: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    changed: list[str] = []
    for rel, data in sorted(expected.items(), key=lambda item: item[0].as_posix()):
        path = skill / rel
        actual = path.read_bytes() if path.exists() else None
        if actual == data:
            continue
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            changed.append(rel.as_posix())
        else:
            errors.append(
                f"{rel.as_posix()} is missing or differs from references/contract-graph.yaml"
            )

    expected_prompt_paths = {
        rel for rel in expected if rel.parts and rel.parts[0] == "prompts"
    }
    for path in sorted((skill / "prompts").glob("[0-9][0-9]-*.md")):
        rel = path.relative_to(skill)
        if rel not in expected_prompt_paths:
            if args.write:
                path.unlink()
                changed.append(f"removed:{rel.as_posix()}")
            else:
                errors.append(
                    f"{rel.as_posix()} is not declared by references/contract-graph.yaml"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    action = "updated" if args.write else "verified"
    print(f"contract views {action}: {len(expected)} files")
    for item in changed:
        print(f"  {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
