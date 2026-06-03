#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "zero-to-hero"


def run(args: list[str]) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    run([sys.executable, str(SKILL / "scripts" / "zero_to_hero_check.py"), str(SKILL), "--deep", "--max-seconds", "240", "--summary"])
    run([sys.executable, str(SKILL / "scripts" / "prompt_sequence_check.py"), str(SKILL)])
    run([sys.executable, str(SKILL / "scripts" / "yaml_parse_check.py"), str(SKILL)])
    print("skill smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
