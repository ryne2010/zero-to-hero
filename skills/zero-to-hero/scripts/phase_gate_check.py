#!/usr/bin/env python3
"""Verify that every derived phase gate exactly matches the contract graph."""

from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True

from zero_to_hero_contract import (  # noqa: E402
    ContractError,
    load_graph,
    rendered_phase_views,
)


def main() -> int:
    skill = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not (skill / "SKILL.md").is_file():
        skill = skill / ".agents" / "skills" / "zero-to-hero"
    try:
        graph = load_graph(skill)
    except ContractError as exc:
        print(f"contract graph invalid: {exc}")
        return 1
    failures: list[str] = []
    for relative, expected in rendered_phase_views(graph).items():
        path = skill / relative
        if not path.is_file():
            failures.append(f"missing {relative}")
        elif path.read_bytes() != expected:
            failures.append(f"derived phase view drift: {relative}")
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print(f"phase gates: PASS ({len(graph['phases'])} phases from contract graph)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
