#!/usr/bin/env python3
"""Validate the recorded *historical* Drive custody claim, not live Drive bytes.

Never upgrade a metadata match into proof that the Drive files are still
accessible or that current main is backed up. The underlying one-time restore
witness lives in the owning GitHub PR.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs/operations/main-history-custody.json"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
DRIVE_ID = re.compile(r"[A-Za-z0-9_-]{15,}\Z")


def _pairs_no_duplicates(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("duplicate custody key: " + k)
        result[k] = v
    return result


def load(path=DEFAULT):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=_pairs_no_duplicates)


def validate(data):
    if type(data) is not dict or data.get("schema") != "ur-main-history-drive-custody/1":
        raise ValueError("unsupported custody schema")
    if data.get("status") != "historically_verified_at_source_commit":
        raise ValueError("must label historical, not current, custody")
    if data.get("scope") != "committed_main_git_history_only":
        raise ValueError("do not claim whole GitHub account recovery")
    if data.get("live_drive_state") != "not_continuously_monitored":
        raise ValueError("Drive bytes must remain unverified between readbacks")
    if data.get("release_qa_credit") is not False:
        raise ValueError("backup cannot grant release gate credit")
    source = data.get("source_commit")
    if not isinstance(source, str) or not HEX40.fullmatch(source):
        raise ValueError("invalid pinned source commit")
    if data.get("github_commit") != source:
        raise ValueError("GitHub bundle commit differs from source")
    digest = data.get("bundle_sha256")
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        raise ValueError("missing bundle sha256")
    count, length = data.get("main_history_commits"), data.get("bundle_bytes")
    if type(count) is not int or count <= 0 or type(length) is not int or length <= 0:
        raise ValueError("invalid restored size/ancestry count")
    if type(data.get("github_actions_run_id")) is not int or data["github_actions_run_id"] <= 0:
        raise ValueError("invalid source run ID")
    try:
        from datetime import date
        date.fromisoformat(data["verification_date_utc"])
    except (TypeError, KeyError, ValueError):
        raise ValueError("invalid verification date") from None
    ids = [data.get("drive_folder_id"), data.get("manifest_drive_id")]
    parts = data.get("parts")
    if not isinstance(parts, list) or not 1 <= len(parts) <= 12:
        raise ValueError("invalid part list")
    seen = set()
    byte_total = 0
    for index, part in enumerate(parts, start=1):
        if type(part) is not dict or part.get("number") != f"{index:02d}":
            raise ValueError("missing or out-of-order part")
        did, digest = part.get("drive_id"), part.get("sha256")
        if not isinstance(did, str) or not DRIVE_ID.fullmatch(did):
            raise ValueError("invalid part Drive ID")
        if type(part.get("bytes")) is not int or not 0 < part["bytes"] <= 80 * 1024 * 1024:
            raise ValueError("part exceeds safe transfer cap")
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            raise ValueError("invalid part digest")
        if digest in seen:
            raise ValueError("duplicate part digest; inspect exact evidence")
        seen.add(digest)
        ids.append(did)
        byte_total += part["bytes"]
    if byte_total != length:
        raise ValueError("part length sum differs from original bundle length")
    if any(not isinstance(i, str) or not DRIVE_ID.fullmatch(i) for i in ids):
        raise ValueError("missing Drive item identity")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate Drive item identity")
    checks = data.get("checks")
    required = {
        "drive_folder_private_owner_only",
        "all_six_drive_items_read_back",
        "all_drive_zip_sha256_match_github_artifact_zip",
        "all_inner_part_sha256_verified",
        "reassembled_bundle_sha256_verified",
        "independent_git_clone_head_matched",
        "git_fsck_connectivity_passed",
        "restored_ancestor_count_matched",
    }
    if type(checks) is not dict or set(checks) != required or any(v is not True for v in checks.values()):
        raise ValueError("missing recorded independent restoration checks")
    evidence = data.get("evidence")
    if not isinstance(evidence, str) or not evidence.startswith(
            "https://github.com/gamesbyian/UR-Recomp/pull/"):
        raise ValueError("missing public verification provenance")
    if type(data.get("exclusions")) is not list or len(data["exclusions"]) < 5:
        raise ValueError("backup scope exclusions must be explicit")
    return {
        "source_commit": source, "commit_count": count, "bundle_bytes": length,
        "verification_date_utc": data["verification_date_utc"],
        "part_count": len(parts), "custody_type": "historical_not_live",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--receipt", type=Path, default=DEFAULT)
    args = ap.parse_args()
    print(json.dumps(validate(load(args.receipt)), sort_keys=True))


if __name__ == "__main__":
    main()
