#!/usr/bin/env python3
"""Read-only, conservative handoff-drift hints from *observed* merged GitHub PRs.

The curated recovery index remains authoritative for recorded candidate state.
A PR referencing a Drive ID is NOT proof that every member was integrated.
Output only flags candidates requiring current-source independent reconciliation.
Input PR JSON comes from GitHub's REST /pulls?state=closed (all pages needed).
"""
import argparse
import json
from pathlib import Path
import re

SHA = re.compile(r"[0-9a-f]{40}\Z")
DRIVE = re.compile(r"[A-Za-z0-9_-]{15,}\Z")
UNRESOLVED = {"blocked", "pending_review", "unknown", "research_only"}


def _mentions_id(text, file_id):
    # Avoid accidental substring matches inside another longer Drive ID.
    return bool(re.search(r"(?<![A-Za-z0-9_-])" + re.escape(file_id) +
                          r"(?![A-Za-z0-9_-])", text))


def scan(registry, pull_requests):
    if (not isinstance(registry, dict) or
            registry.get("schema") != "ur-recovery-registry/1" or
            registry.get("scope") != "curated_not_exhaustive" or
            not isinstance(registry.get("candidates"), list)):
        raise ValueError("invalid curated recovery registry")
    if not isinstance(pull_requests, list):
        raise ValueError("PR census must be an array")
    merged = []
    for pr in pull_requests:
        if not isinstance(pr, dict):
            raise ValueError("invalid PR entry")
        number, sha = pr.get("number"), pr.get("merge_commit_sha")
        when = pr.get("merged_at")
        if when is None:
            continue
        if (type(number) is not int or number < 1 or
                not isinstance(sha, str) or not SHA.fullmatch(sha) or
                not isinstance(when, str) or not when):
            raise ValueError("incomplete merged PR receipt")
        merged.append(pr)
    hints = []
    for item in registry["candidates"]:
        if not isinstance(item, dict):
            raise ValueError("invalid registry candidate")
        if item.get("state") not in UNRESOLVED:
            continue
        drive_id = item.get("drive_id")
        if not isinstance(drive_id, str) or not DRIVE.fullmatch(drive_id):
            raise ValueError("invalid unresolved Drive identity")
        for pr in merged:
            # Only authored description, not titles or PR filenames.
            body = pr.get("body") or ""
            if not isinstance(body, str):
                raise ValueError("invalid PR description")
            if _mentions_id(body, drive_id):
                hints.append({
                    "candidate_id": item["candidate_id"],
                    "work_id": item["work_id"],
                    "recorded_state": item["state"],
                    "drive_id": drive_id,
                    "linked_merged_pr": pr["number"],
                    "merge_sha": pr["merge_commit_sha"],
                    "conclusion": "REVIEW_POSSIBLE_STALE_DISPOSITION",
                    "warning": ("PR mentions exact Drive ID; inspect merged diff and "
                                "all archive members before changing candidate state"),
                })
    return {
        "registry_scope": "curated_not_exhaustive",
        "merged_prs_checked": len(merged),
        "candidate_count": len(registry["candidates"]),
        "hints": sorted(hints, key=lambda x: (x["candidate_id"], x["linked_merged_pr"])),
        "automatic_state_changes": 0,
        "release_gate_credit": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", type=Path, default=Path("docs/recovery/agent-candidates.json"))
    p.add_argument("--pulls-json", type=Path, required=True,
                   help="Actual complete /pulls?state=closed GitHub API response; do not invent")
    args = p.parse_args()
    result = scan(json.loads(args.registry.read_text(encoding="utf-8")),
                  json.loads(args.pulls_json.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
