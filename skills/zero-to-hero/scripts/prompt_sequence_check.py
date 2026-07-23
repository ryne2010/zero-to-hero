#!/usr/bin/env python3
"""Verify prompt order and every machine-rendered phase prompt contract."""
from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from zero_to_hero_contract import (  # noqa: E402
    ContractError,
    graph_prompts,
    load_graph,
    render_prompt,
    skill_root_from,
)

REQUIRED_HEADINGS = [
    "## Goal",
    "## Context and required reads",
    "## Entry criteria",
    "## Constraints",
    "## Allowed writes",
    "## Forbidden writes",
    "## Expected outputs",
    "## Evidence and checks",
    "## Stop or block when",
    "## Done when",
    "## Runtime implementation boundary",
]


def main() -> int:
    try:
        skill = skill_root_from(sys.argv[1] if len(sys.argv) > 1 else ".")
        graph = load_graph(skill)
    except ContractError as exc:
        print(f"prompt contract: failed: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    previous = -1
    for contract in graph_prompts(graph):
        order = int(contract["order"])
        if order <= previous:
            errors.append(f"non-ascending prompt order at {contract['id']}")
        previous = order
        path = skill / "prompts" / contract["prompt_file"]
        if not path.is_file():
            errors.append(f"missing prompt {path.relative_to(skill)}")
            continue
        actual = path.read_text(encoding="utf-8")
        expected = render_prompt(
            contract,
            global_forbidden_write_paths=graph["global_forbidden_write_paths"],
        )
        if actual != expected:
            errors.append(
                f"{path.relative_to(skill)} is not the graph-rendered prompt view"
            )
        for heading in REQUIRED_HEADINGS:
            if actual.count(heading) != 1:
                errors.append(
                    f"{path.relative_to(skill)} must contain exactly one {heading!r}"
                )
        if "Do not implement" not in actual and "Never implement" not in actual:
            errors.append(
                f"{path.relative_to(skill)} lacks explicit no-runtime implementation boundary"
            )

    declared = {
        contract["prompt_file"] for contract in graph_prompts(graph)
    }
    extras = sorted(
        path.name
        for path in (skill / "prompts").glob("[0-9][0-9]-*.md")
        if path.name not in declared
    )
    if extras:
        errors.append(f"undeclared prompt files: {extras}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"prompt contracts: passed ({len(declared)} prompts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
