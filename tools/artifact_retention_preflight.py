#!/usr/bin/env python3
"""Read-only GitHub Actions artifact availability, provenance and expiry preflight.

Metadata proves at most an artifact *may* be downloaded. No byte inspection,
evidence authentication, automatic retention, release credit or GitHub write.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

HEX40 = re.compile(r"[a-f0-9]{40}\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SCHEMA = "UR-CI-ARTIFACT-AVAILABILITY/1"
MAX_ARTIFACTS = 100


def require(ok, why):
    if not ok:
        raise ValueError(why)


def when(value):
    require(isinstance(value, str), "timestamp missing")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp malformed") from exc
    require(result.tzinfo is not None, "timestamp lacks timezone")
    return result.astimezone(timezone.utc)


def github_get(repo, suffix):
    require(isinstance(repo, str) and bool(REPO.fullmatch(repo)),
            "invalid repository")
    require(re.fullmatch(r"actions/runs/[1-9][0-9]*(?:/artifacts\?per_page=100)?", suffix),
            "unsupported read-only endpoint")
    proc = subprocess.run(
        ["gh", "api", f"repos/{repo}/{suffix}"],
        capture_output=True, text=True, timeout=30, check=False)
    require(proc.returncode == 0, "GitHub metadata unavailable")
    require(len(proc.stdout) < 2_000_000, "oversized metadata")
    return json.loads(proc.stdout)


def inspect(run, listing, *, expected_sha=None, now=None, warning_hours=48):
    """Fail-closed on inconsistent identity, bounded listings and bad dates."""
    require(isinstance(run, dict) and isinstance(listing, dict),
            "run and listing must be objects")
    require(type(run.get("id")) is int and run["id"] > 0,
            "invalid GitHub run ID")
    require(run.get("status") in ("queued", "in_progress", "completed",
                                 "waiting", "requested", "pending"),
            "unknown run status")
    head = run.get("head_sha")
    require(isinstance(head, str) and bool(HEX40.fullmatch(head)),
            "run not bound to exact SHA")
    require(expected_sha is None or isinstance(expected_sha, str)
            and bool(HEX40.fullmatch(expected_sha)),
            "expected SHA must be exact 40-character commit")
    require(type(warning_hours) is int and 1 <= warning_hours <= 720,
            "invalid warning interval")
    now = when(now) if isinstance(now, str) else (
        datetime.now(timezone.utc) if now is None else now)
    require(isinstance(now, datetime) and now.tzinfo is not None,
            "invalid inspection time")
    now = now.astimezone(timezone.utc)
    rows = listing.get("artifacts")
    total = listing.get("total_count")
    require(type(total) is int and total >= 0 and
            isinstance(rows, list) and len(rows) <= MAX_ARTIFACTS,
            "invalid GitHub artifact page")
    # A full page might be truncated even if count is accidentally stale.
    census_complete = total == len(rows) and len(rows) < MAX_ARTIFACTS
    entries, ids = [], set()
    source_matches = (None if expected_sha is None else expected_sha == head)
    producer_passed = (run.get("status") == "completed"
                       and run.get("conclusion") == "success")
    for row in rows:
        require(isinstance(row, dict), "invalid artifact record")
        ident = row.get("id")
        require(type(ident) is int and ident > 0 and ident not in ids,
                "duplicate or malformed artifact ID")
        ids.add(ident)
        producer = row.get("workflow_run")
        require(isinstance(producer, dict)
                and producer.get("id") == run["id"]
                and producer.get("head_sha") == head,
                "artifact belongs to different run/source")
        name = row.get("name")
        require(isinstance(name, str) and 0 < len(name) <= 150,
                "invalid artifact name")
        digest = row.get("digest")
        # A missing digest means hash verification is unavailable, NOT that
        # the artifact is safe to reuse.
        hash_value = None
        if digest is not None:
            require(isinstance(digest, str)
                    and digest.startswith("sha256:")
                    and bool(HEX64.fullmatch(digest[7:])),
                    "unsupported artifact digest")
            hash_value = digest[7:]
        created, expires = when(row.get("created_at")), when(row.get("expires_at"))
        require(expires >= created, "artifact expiry predates creation")
        require(type(row.get("expired")) is bool, "missing artifact expiry status")
        size = row.get("size_in_bytes")
        require(type(size) is int and size >= 0, "invalid artifact size")
        remaining = (expires - now).total_seconds() / 3600
        invalid = row["expired"] or remaining <= 0
        if invalid:
            state = "expired_or_unavailable"
        elif not producer_passed:
            state = "producer_not_successful"
        elif source_matches is not True:
            state = "source_unqualified"
        elif hash_value is None or size == 0:
            state = "digest_or_bytes_missing"
        elif remaining <= warning_hours:
            state = "expiry_urgent_review"
        else:
            state = "metadata_ready_for_independent_byte_audit"
        entries.append({
            "artifact_id": ident, "name": name, "size_in_bytes": size,
            "reported_outer_sha256": hash_value,
            "created_at": created.isoformat(), "expires_at": expires.isoformat(),
            "remaining_hours_at_inspection": round(remaining, 2),
            "availability": state,
            "authoritative_release_evidence": False,
        })
    return {
        "schema": SCHEMA,
        "authority": "github_metadata_only_zero_release_credit",
        "run_id": run["id"], "run_name": str(run.get("name", ""))[:100],
        "run_head_sha": head, "expected_sha": expected_sha,
        "source_matches_expected": source_matches,
        "run_conclusion": run.get("conclusion"),
        "producer_passed": producer_passed,
        "inspected_at": now.isoformat(),
        "artifact_census_complete": census_complete,
        "artifact_count_observed": len(entries),
        "artifact_count_reported": total,
        "artifacts": entries,
        "release_gate_credit": 0,
        "limits": [
            "GitHub artifact metadata is not a bytes check or authenticated release witness.",
            "Workflow head SHA may differ from the built checkout; open the original manifest.",
            "An unexpired artifact may still fail to download; validate original SHA256 after retrieval.",
            "Artifact absence/expiry is not evidence that the underlying work never occurred.",
            "Do not reupload restricted ROM, save-state, personal or third-party data to extend retention.",
            "A different executable or private ZIP digest is a distinct release candidate.",
        ],
    }


def markdown(report):
    lines = [
        "# Artifact availability and retention preflight", "",
        "Producer run: " + str(report["run_id"]) + " " + report["run_name"],
        "Run source: " + report["run_head_sha"],
        "Expected source match: " + str(report["source_matches_expected"]),
        "Producer passed: " + str(report["producer_passed"]),
        "Artifact census: " + ("complete" if report["artifact_census_complete"]
                               else "INCOMPLETE/UNKNOWN"),
        "No private data opened, no release QA credit.", "",
    ]
    for x in report["artifacts"]:
        lines.append(f"- Artifact {x['artifact_id']} {x['name']}: {x['availability']}; "
                     f"{x['remaining_hours_at_inspection']} h until API expiry; "
                     f"outer SHA256 {x['reported_outer_sha256'] or 'unavailable'}")
    lines.extend(["", "## Meaning", "",
                  "An available matching artifact is only ready for **independent byte review**.",
                  "If expiration is imminent, ask the authorized evidence owner to preserve "
                  "a rights-safe receipt. Do not publish private bytes.",
                  "No gameplay, hardware, private ZIP or source-original equivalence established."])
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--live-run-id", type=int)
    src.add_argument("--saved-run", type=Path)
    p.add_argument("--saved-artifacts", type=Path)
    p.add_argument("--repo", default="gamesbyian/UR-Recomp")
    p.add_argument("--expected-sha")
    p.add_argument("--warning-hours", type=int, default=48)
    p.add_argument("--json-out", type=Path)
    p.add_argument("--markdown-out", type=Path)
    args = p.parse_args()
    if args.live_run_id is not None:
        require(args.saved_artifacts is None, "live run cannot take saved artifact page")
        require(args.live_run_id > 0, "invalid run ID")
        run = github_get(args.repo, f"actions/runs/{args.live_run_id}")
        listing = github_get(args.repo, f"actions/runs/{args.live_run_id}/artifacts?per_page=100")
    else:
        require(args.saved_artifacts is not None, "saved run needs saved artifact metadata")
        run = json.loads(args.saved_run.read_text(encoding="utf-8"))
        listing = json.loads(args.saved_artifacts.read_text(encoding="utf-8"))
    report = inspect(run, listing, expected_sha=args.expected_sha,
                     warning_hours=args.warning_hours)
    view = markdown(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(view)
    print(view, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
