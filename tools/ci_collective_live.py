#!/usr/bin/env python3
"""Read-only GitHub verification of a frozen collective candidate.

Proves live PR identity, compare ancestry and unchanged member file blobs;
not adequacy/execution of CI tests, active-writer freedom or acceptance.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

try:
    from .ci_collective_candidate import validate_manifest
except ImportError:
    from ci_collective_candidate import validate_manifest

SHA = re.compile(r"[0-9a-f]{40}\Z")
REPO = "gamesbyian/UR-Recomp"
MAX_FILES = 300


def sha(value: Any, what: str) -> str:
    if type(value) is not str or not SHA.fullmatch(value):
        raise ValueError("invalid live SHA: " + what)
    return value


def required_dict(value: Any, description: str) -> dict:
    if type(value) is not dict:
        raise ValueError("missing or malformed " + description)
    return value


def live_attest(manifest: dict, fetch: Callable[[str], Any], repo: str = REPO) -> dict:
    """Fail closed on moved heads, missing pages, conflicting paths and bytes.

    fetch is a read-only API function returning None on 404, decoded JSON
    on success, or raising on transport errors. This is only source evidence.
    """
    validate_manifest(manifest)
    if repo != REPO:
        raise ValueError("repository not in allowlist")
    stem = "/repos/" + repo
    main_url = stem + "/branches/main"

    def main_head() -> str:
        info = required_dict(fetch(main_url), "main branch")
        return sha(required_dict(info.get("commit"), "main commit").get("sha"), "main head")

    if main_head() != manifest["base_sha"]:
        raise ValueError("main moved since candidate base was frozen")

    candidate = manifest["candidate_sha"]
    exact_commit = required_dict(fetch(stem + "/commits/" + candidate), "candidate commit")
    if sha(exact_commit.get("sha"), "candidate commit") != candidate:
        raise ValueError("candidate commit was not fetched by exact SHA")

    # Ancestry alone cannot prove that file bytes survived conflict resolution.
    for ancestor in [manifest["base_sha"]] + [m["head_sha"] for m in manifest["members"]]:
        compared = required_dict(fetch(stem + "/compare/" + ancestor + "..." + candidate), "ancestry")
        if compared.get("status") not in ("ahead", "identical") or compared.get("behind_by") != 0:
            raise ValueError("candidate is not descendant of " + ancestor[:12])

    checked_blobs = 0
    checked_deleted = 0
    all_live_paths: set[str] = set()
    results: list[dict] = []
    for member in manifest["members"]:
        n = member["pr"]
        url = stem + "/pulls/" + str(n)
        pr = required_dict(fetch(url), "PR")
        if (pr.get("number") != n or pr.get("state") != "open"
                or pr.get("draft") is not False or pr.get("mergeable") is not True):
            raise ValueError("PR is not open, ready and confirmed mergeable: " + str(n))
        base = required_dict(pr.get("base"), "PR base")
        head = required_dict(pr.get("head"), "PR head")
        if (base.get("ref") != "main" or
                required_dict(base.get("repo"), "PR base repository").get("full_name") != repo or
                required_dict(head.get("repo"), "PR head repository").get("full_name") != repo or
                sha(head.get("sha"), "PR head") != member["head_sha"]):
            raise ValueError("PR base/head changed: " + str(n))
        expected_count = pr.get("changed_files")
        if type(expected_count) is not int or not 1 <= expected_count <= MAX_FILES:
            raise ValueError("unavailable or unsupported PR file count: " + str(n))
        file_rows: list[dict] = []
        for page in range(1, MAX_FILES // 100 + 2):
            rows = fetch(url + "/files?per_page=100&page=" + str(page))
            if type(rows) is not list or len(rows) > 100:
                raise ValueError("malformed PR file page")
            if any(type(row) is not dict for row in rows):
                raise ValueError("malformed PR file row")
            file_rows.extend(rows)
            if len(file_rows) > MAX_FILES:
                raise ValueError("PR exceeds pilot file cap")
            if len(rows) < 100:
                break
        else:
            raise ValueError("PR file pages truncated")
        if len(file_rows) != expected_count:
            raise ValueError("PR file census incomplete: " + str(n))

        file_paths: set[str] = set()
        for row in file_rows:
            status = row.get("status")
            if status not in ("added", "modified", "removed", "renamed", "copied", "changed"):
                raise ValueError("unsupported PR file status")
            path = row.get("filename")
            if type(path) is not str or path in file_paths:
                raise ValueError("duplicate or malformed live file path")
            file_paths.add(path)
            if status == "renamed":
                prior = row.get("previous_filename")
                if type(prior) is not str or prior in file_paths:
                    raise ValueError("malformed rename source")
                file_paths.add(prior)
            if file_paths & all_live_paths:
                raise ValueError("live changed-file collision between members")
            if status == "removed":
                absent_paths = [path]
            elif status == "renamed":
                absent_paths = [row["previous_filename"]]
            else:
                absent_paths = []
            for gone in absent_paths:
                qpath = urllib.parse.quote(gone, safe="/")
                qsha = urllib.parse.quote(candidate, safe="")
                if fetch(stem + "/contents/" + qpath + "?ref=" + qsha) is not None:
                    raise ValueError("deleted/renamed source path survived: " + gone)
                checked_deleted += 1
            if status != "removed":
                source_blob = sha(row.get("sha"), "PR file blob")
                qpath = urllib.parse.quote(path, safe="/")
                qsha = urllib.parse.quote(candidate, safe="")
                candidate_file = required_dict(
                    fetch(stem + "/contents/" + qpath + "?ref=" + qsha), "candidate file")
                if (candidate_file.get("type") not in ("file", "symlink", "submodule") or
                        sha(candidate_file.get("sha"), "candidate blob") != source_blob):
                    raise ValueError("candidate changed member file bytes: " + path)
                checked_blobs += 1
        if file_paths != set(member["changed_paths"]):
            raise ValueError("declared/live changed-file paths mismatch: " + str(n))
        if file_paths & all_live_paths:
            raise ValueError("live inter-member path collision: " + str(n))
        all_live_paths.update(file_paths)
        current = required_dict(fetch(url), "PR closing read")
        if (required_dict(current.get("head"), "closing PR head").get("sha") != member["head_sha"]
                or current.get("changed_files") != expected_count or current.get("draft") is not False
                or current.get("state") != "open"):
            raise ValueError("PR changed during inspection: " + str(n))
        results.append({"pr": n, "work_id": member["work_id"], "head_sha": member["head_sha"],
                        "file_rows": expected_count, "affected_paths": len(file_paths)})

    if main_head() != manifest["base_sha"]:
        raise ValueError("main moved during inspection")
    return {"status": "live-source-attested-only", "batch_id": manifest["batch_id"],
            "base_sha": manifest["base_sha"], "candidate_sha": candidate,
            "members": results, "file_blob_matches": checked_blobs,
            "removed_paths_confirmed_absent": checked_deleted,
            "affected_paths": len(all_live_paths), "live_main_and_pr_heads_checked": True,
            "candidate_ancestry_and_member_files_checked": True,
            "independent_writer_clearance": False,
            "complete_required_tests_executed": False, "release_accepted": False,
            "personal_hp_pr_code_execution_authorized": False}


def github_fetch(path: str) -> Any:
    if not path.startswith("/repos/" + REPO + "/"):
        raise ValueError("API route outside repository allowlist")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    request = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "ur-collective-read-only/1",
                 **({"Authorization": "Bearer " + token} if token else {})})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError("GitHub read failed: HTTP " + str(exc.code)) from None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        candidate = json.loads(args.manifest.read_text(encoding="utf-8"))
        receipt = live_attest(candidate, github_fetch)
    except (OSError, UnicodeError, ValueError, TypeError, RuntimeError,
            urllib.error.URLError, json.JSONDecodeError) as exc:
        parser.exit(2, "LIVE CANDIDATE REJECTED: " + str(exc) + "\n")
    print(json.dumps(receipt, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
