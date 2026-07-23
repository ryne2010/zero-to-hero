#!/usr/bin/env python3
"""Inventory UI visual assets in docs/ui."""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXTS={".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}
if __name__ == "__main__":
    repo=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
    roots=[repo/"docs/ui/visual-assets", repo/"docs/screens"]
    assets=[]
    for r in roots:
        if r.exists():
            for p in r.rglob("*"):
                if p.suffix.lower() in EXTS:
                    assets.append(str(p.relative_to(repo)))
    print(json.dumps({"count": len(assets), "assets": assets}, indent=2))
