#!/usr/bin/env python3
"""Inventory zero-to-hero harness layers in a target repo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAYERS = {
    "source_of_truth_contract": ["docs/00-meta/source-of-truth-map.yaml", "docs/00-meta/feature-index.yaml"],
    "frontend_parity_system": ["docs/ui/frontend-parity-system", "docs/ui/frontend-builder-context.md"],
    "product_usability_contract": ["docs/product-execution/action-binding-matrix.yaml", "docs/product-execution/app-usability-contract.md"],
    "runtime_evidence_harness": ["docs/product-execution/runtime-evidence", "scripts/runtime-evidence-check.mjs"],
    "coverage_traceability_harness": ["docs/product-execution/traceability", "scripts/coverage-traceability-check.mjs"],
    "local_provider_simulators": ["docs/product-execution/local-simulators", "scripts/local-provider-simulator-check.mjs"],
    "state_machine_harness": ["docs/product-execution/state-machines"],
    "negative_path_harness": ["docs/product-execution/negative-paths"],
    "role_walkthrough_harness": ["docs/product-execution/role-walkthroughs"],
    "observability_harness": ["docs/product-execution/observability"],
    "local_product_done_gate": ["docs/product-execution/local-product-done-gate.md", "scripts/verify-local-product.mjs"],
    "repo_scoped_skills": [".agents/skills"],
    "neutral_implementation_handoff": [
        "docs/implementation/IMPLEMENTATION_BRIEF.md",
        "docs/implementation/EXECPLAN.md",
        "docs/implementation/PLANNING_EVIDENCE.md",
        "scripts/zero_to_hero_handoff_check.py",
        "PLANS.md",
    ],
}

def exists(repo: Path, rel: str) -> bool:
    return (repo/rel).exists()

if __name__ == "__main__":
    repo=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
    report={}
    for layer, paths in LAYERS.items():
        present=[p for p in paths if exists(repo,p)]
        report[layer]={"status": "present" if len(present)==len(paths) else "partial" if present else "missing", "present": present, "expected": paths}
    print(json.dumps(report, indent=2, sort_keys=True))
