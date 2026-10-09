#!/usr/bin/env python3
"""Measure UR's ordered framework patch compatibility against Ema's pinned fork.

Experimental scratch clone ONLY. Successful git apply is syntactic evidence,
not binary ABI compatibility, behavior parity, or permission to re-pin main.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def assess(repo_root: Path, framework: Path) -> dict:
    tool = json.loads((repo_root / "tools/toolchain-entries/snesrecomp.json").read_text(encoding="utf-8"))
    results = []
    for position, spec in enumerate(tool["patches"], 1):
        patch = repo_root / spec["path"]
        data = patch.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha != spec["sha256"]:
            raise ValueError(f"Invalid manifest hash at patch {position}: {patch}")
        check = subprocess.run(["git", "apply", "--check", str(patch)], cwd=framework,
                               capture_output=True, text=True)
        if check.returncode == 0:
            result = subprocess.run(["git", "apply", str(patch)], cwd=framework,
                                    capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Race between --check and apply: {patch}: {result.stderr}")
            status = "applied_in_scratch_fork"
            detail = None
        else:
            status = "conflict_or_missing_anchor"
            detail = check.stderr.strip()[:2000]
        results.append({
            "order": position, "path": spec["path"],
            "sha256": spec["sha256"], "status": status,
            "diagnostic": detail,
        })
        print(f"[{position:02d}/{len(tool['patches'])}] {status} {spec['path']}", flush=True)
    applied = sum(r["status"] == "applied_in_scratch_fork" for r in results)
    return {
        "schema_version": 1,
        "source_ur_framework": "cd5875cbdaf19f5e324272b1f8051d671fce9215",
        "candidate_baldosa_framework": "075fbe4c8e0d97b0013be541795c39cb644a9709",
        "total_ordered_patches": len(results),
        "applied_in_scratch_fork": applied,
        "conflict_or_missing_anchor": len(results) - applied,
        "remainder_requires_semantic_integration": True,
        "all_writable_changes_disposable": True,
        "meaning": "Sequential git-apply compatibility in a scratch clone, not actual game runtime correctness",
        "patches": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--framework", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    data = assess(args.project.resolve(), args.framework.resolve())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("Applied", data["applied_in_scratch_fork"], "/", data["total_ordered_patches"],
          "in disposable fork. No runtime tested.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
