#!/usr/bin/env python3
"""Fail closed when the progress log is behind the explicitly supplied reviewed source."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def check(inventory, log, expected_head):
    if inventory.get("version") != "windows-beta-v1":
        raise ValueError("Unexpected frozen inventory version")
    entries = log.get("entries", [])
    if not entries:
        raise ValueError("No progress entries")
    last = entries[-1]
    if last.get("source_commit") != expected_head:
        raise ValueError("STALE: log reviewed source %s != requested %s" % (last.get("source_commit"), expected_head))
    if "engineering_maturity_after" not in last:
        raise ValueError("Latest progress entry lacks a measured inventory score")
    if not last.get("changes"):
        raise ValueError("Latest progress entry has no documented evidence changes")
    for change in last["changes"]:
        if not str(change.get("evidence", "")).startswith("https://github.com/gamesbyian/UR-Recomp/"):
            raise ValueError("Progress evidence URL missing or outside repository")
    return last

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reviewed-head", required=True, help="Full 40-digit commit SHA of source reviewed; never assume local checkout HEAD")
    p.add_argument("--inventory", type=Path, default=ROOT / "docs/PROGRESS-INVENTORY.json")
    p.add_argument("--changelog", type=Path, default=ROOT / "docs/PROGRESS-CHANGELOG.json")
    a = p.parse_args()
    if len(a.reviewed_head) != 40 or any(c not in "0123456789abcdef" for c in a.reviewed_head):
        p.error("reviewed-head must be lowercase full 40-digit SHA")
    row = check(json.loads(a.inventory.read_text()),json.loads(a.changelog.read_text()),a.reviewed_head)
    print("Reviewed through %s; maturity %.2f%%; %d evidence changes recorded" %
          (a.reviewed_head, row["engineering_maturity_after"], len(row["changes"])))

if __name__ == "__main__":
    main()
