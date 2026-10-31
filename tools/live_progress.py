#!/usr/bin/env python3
"""Live progress: always reports current HEAD and bounded, source-pinned uncertainty.

Historical acceptance is a FLOOR, never advertised as latest certified HEAD.
Unreviewed commits are assessed as a queue, not silently assigned points.
Requires local git checkout; no network or third-party libraries.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()

def summarize(inventory, ledger, reviewed, head, commits):
    from tools.atomic_progress_v2 import validate
    from tools.remaining_work_forecast import calculate
    progress = validate(inventory, ledger)
    outstanding = [c for c in inventory["criteria"] if c["status"] != "bounded_verified"]
    # This is a mathematically safe UNCERTAINTY ENVELOPE, not a prediction:
    # unreviewed work may have completed nothing, some or all outstanding criteria.
    # Never assign the optimistic edge as a scored outcome.
    lower = progress["bounded_product_coverage_percent"]
    upper = 100.0 if commits else lower
    return {
        "current_main_sha": head,
        "last_criterion_reviewed_sha": reviewed,
        "review_covers_current_head": head == reviewed,
        "unreviewed_commits": commits,
        "verified_bounded_coverage_percent": lower,
        "possible_current_coverage_interval_percent": [lower, upper],
        "interval_interpretation": "logical bounds, NOT calibrated probability or estimated completion",
        "unverified_criteria": [c["id"] for c in outstanding],
        "unverified_criteria_count": len(outstanding),
        "independently_reviewed_bounded_percent": progress["independently_audited_coverage_percent"],
        "accepted_USA_events": progress["independent_USA_complete_events"],
        "release_gates_passed": progress["formal_windows_gates_passed"],
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json","markdown"), default="markdown")
    args = parser.parse_args()
    inv = json.loads((ROOT/"docs/progress/windows-beta-v2-inventory.json").read_text())
    ledger = json.loads((ROOT/"docs/RELEASE-QUALITY-LEDGER.json").read_text())
    pointer = json.loads((ROOT/"docs/progress/current-v2-review.json").read_text())
    reviewed = pointer["reviewed_main_sha"]
    head = git("rev-parse","HEAD")
    try:
        git("merge-base","--is-ancestor",reviewed,head)
    except subprocess.CalledProcessError as e:
        parser.error("Reviewed source is not an ancestor of this checkout; reconcile before reporting")
    n = int(git("rev-list","--count",f"{reviewed}..{head}"))
    summary = summarize(inv,ledger,reviewed,head,n)
    changes = git("log", "--format=%H%x09%s", f"{reviewed}..{head}").splitlines() if n else []
    patterns = {
        "ONE": ("one-", "tour", "practice", "result", "race"),
        "TWO": ("two-", "2p", "multiplayer", "seat", "tournament"),
        "MENU": ("menu", "title", "attract", "controller", "root"),
        "DATA": ("data-", "profile", "record", "unicode", "replay", "ghost"),
        "RECOVERY": ("recovery", "win-boot", "migration", "save", "ntfs"),
        "WIDE": ("wide-", "hdma", "raster", "4k", "viewport", "graphics"),
        "ART": ("art-", "racer art", "model", "rig", "sprite"),
        "FID": ("qa01", "spc", "apu", "cpu", "zoo", "parity", "fidelity"),
        "QA": ("qa-", "physical", "release", "package"),
    }
    open_prefixes = {c["area"] for c in inv["criteria"] if c["status"] != "bounded_verified"}
    candidates = []
    for line in changes:
        sha, _, subject = line.partition("\t")
        match = sorted(k for k, keys in patterns.items()
                       if k in open_prefixes and any(word in subject.lower() for word in keys))
        if match:
            candidates.append({"sha": sha, "title": subject, "possible_areas": match})
    summary["unreviewed_candidate_commits"] = candidates
    summary["unreviewed_candidate_count"] = len(candidates)
    summary["candidate_warning"] = "Subject-based discovery only; NOT verification or earned completion credit"
    from tools.remaining_work_forecast import calculate
    prior = json.loads((ROOT/"docs/progress/remaining-work-prior-v1.json").read_text())
    adjust = json.loads((ROOT/"docs/progress/remaining-work-adjustments.json").read_text())
    effort = calculate(prior,inv,adjust,samples=500)
    summary["remaining_relative_work_units_prior_mean"] = effort["expected_relative_work_units"]
    summary["effort_estimate_basis"] = "Last reviewed criterion inventory, not rescreened current HEAD"
    if args.format == "json":
        print(json.dumps(summary,indent=2))
    else:
        print("# Live progress status")
        print("HEAD:",head,"| last accepted source:",reviewed)
        print("Verified floor: %.1f%% | independent bounded: %.1f%%" %
              (summary["verified_bounded_coverage_percent"],
               summary["independently_reviewed_bounded_percent"]))
        print("Unreviewed commits:",n,"| unverified criteria at accepted checkpoint:",len(summary["unverified_criteria"]))
        print("Unreviewed candidate commits for evidence triage:",len(candidates))
        for item in candidates[:10]:
            print(" ", item["sha"][:10], "/".join(item["possible_areas"]), item["title"])
        print("Logical completion envelope:",summary["possible_current_coverage_interval_percent"],
              "(not a probabilistic estimate)")
        print("Remaining relative-work prior:",effort["expected_relative_work_units"],
              "(excludes possible unreviewed closures)")
        print("USA:",summary["accepted_USA_events"],"/45 | QA gates:",
              summary["release_gates_passed"],"/12")
        if n:
            print("WARNING: current progress is not independently certified; never present this floor as a fresh score.")
if __name__ == "__main__":
    main()
