#!/usr/bin/env python3
"""Bounded, resumable, metadata-only scheduled intake for public Drive Vault.

Downloads remain exclusively on the ephemeral runner. Published artifacts
contain metadata/hashes/triage, never original ZIPs or extracted source.
No automatic publication, semantic disposition or release gate credit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from vault_gdown_intake import (
    DEFAULT_FOLDER, ID_PATTERN, MAX_SESSION_BYTES, MAX_REVIEW_LEADS,
    list_public_folder, pull,
)

SCHEMA = "ur-vault-recurring-checkpoint/1"
REPORT_SCHEMA = "ur-vault-recurring-intake/1"
MAX_BATCH = 12
MAX_RETAINED_IDS = 500


def read_checkpoint(path: Path | None) -> dict:
    """Reject unrecognized checkpoint shape rather than silently skip work."""
    if path is None or not path.exists():
        return {"schema": SCHEMA, "items": {}}
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise ValueError("incompatible recurring Vault checkpoint")
    items = doc.get("items")
    if not isinstance(items, dict) or len(items) > MAX_RETAINED_IDS:
        raise ValueError("invalid checkpoint items")
    for file_id, item in items.items():
        if (not isinstance(file_id, str) or not ID_PATTERN.fullmatch(file_id)
                or not isinstance(item, dict)
                or not isinstance(item.get("path"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")))
                or not isinstance(item.get("bytes"), int)
                or item["bytes"] < 0
                or not isinstance(item.get("audited_at"), str)):
            raise ValueError("invalid checkpoint member")
        try:
            datetime.fromisoformat(item["audited_at"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("invalid checkpoint timestamp") from exc
        leads = item.get("review_leads", [])
        if not isinstance(leads, list) or len(leads) > MAX_REVIEW_LEADS:
            raise ValueError("invalid checkpoint review leads")
        for lead in leads:
            if (not isinstance(lead, dict)
                    or not isinstance(lead.get("member"), str)
                    or not 0 < len(lead["member"]) <= 512
                    or not re.fullmatch(r"[0-9a-f]{64}", str(lead.get("sha256", "")))
                    or not isinstance(lead.get("bytes"), int)
                    or lead["bytes"] < 0
                    or lead.get("status") != "unmatched_needs_review"
                    or lead.get("kind") not in ("patch", "source_or_test")):
                raise ValueError("invalid checkpoint review lead")
        omitted = item.get("review_leads_filtered_or_truncated", 0)
        if not isinstance(omitted, int) or omitted < 0:
            raise ValueError("invalid checkpoint review lead count")
    failures = doc.get("failures", {})
    if not isinstance(failures, dict) or len(failures) > MAX_RETAINED_IDS:
        raise ValueError("invalid checkpoint failures")
    for file_id, record in failures.items():
        if not ID_PATTERN.fullmatch(file_id) or not isinstance(record, dict):
            raise ValueError("invalid failed-file checkpoint entry")
    return doc


def should_refresh(entry: dict, cached: dict | None, now: datetime,
                   refresh_days: int) -> str | None:
    if not cached:
        return "new"
    if cached["path"] != entry["path"]:
        return "renamed"
    timestamp = datetime.fromisoformat(cached["audited_at"].replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("checkpoint timestamps must include timezone")
    if now - timestamp >= timedelta(days=refresh_days):
        return "refresh_due"
    return None


def make_queue(entries: list[dict], prior: dict, now: datetime,
               refresh_days: int, forced_id: str | None = None,
               recent_failures: set[str] | None = None):
    if forced_id and forced_id not in {entry["id"] for entry in entries}:
        raise ValueError("requested file ID missing from public folder")
    due = []
    skipped = []
    for entry in entries:
        reason = ("explicit_probe" if entry["id"] == forced_id
                  else should_refresh(entry, prior.get(entry["id"]), now, refresh_days))
        item = {**entry, "reason": reason}
        if reason:
            due.append(item)
        else:
            skipped.append(item)
    if forced_id:
        due = [item for item in due if item["id"] == forced_id]
    # ZIPs precede text pointers; first-time candidates precede stale refreshes.
    recent_failures = recent_failures or set()
    due.sort(key=lambda item: (
        item["id"] in recent_failures,
        item["reason"] == "refresh_due",
        not item["path"].lower().endswith(".zip"),
        item["path"].casefold(), item["id"],
    ))
    return due, skipped


def oversized_retry_after(failure: dict | None, entry: dict, now: datetime,
                          refresh_days: int) -> str | None:
    """Avoid repeat downloads of unchanged archives hitting hard size limits.

    Forced probes and renamed paths bypass this cooldown. Other failures stay
    retryable on the next cycle; in-place replacements are rechecked eventually.
    """
    error = str((failure or {}).get("error", ""))
    deterministic_budget_errors = (
        "download exceeds single-file byte budget",
        "expanded ZIP budget exceeded",
        "nested ZIP exceeds byte budget",
    )
    if (not failure or failure.get("path") != entry["path"]
            or not any(reason in error for reason in deterministic_budget_errors)):
        return None
    try:
        attempted = datetime.fromisoformat(
            str(failure["last_attempt"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        return None
    if attempted.tzinfo is None:
        return None
    retry_at = attempted + timedelta(days=refresh_days)
    return retry_at.isoformat() if now < retry_at else None


def run_cycle(*, out: Path, folder_url: str = DEFAULT_FOLDER,
              previous: Path | None = None, max_files: int = 3,
              max_total_bytes: int = 64 * 1024 * 1024,
              refresh_days: int = 14, forced_id: str | None = None,
              now: datetime | None = None, enumerator=list_public_folder,
              downloader=pull, git_tree: bytes | None = None) -> tuple[dict, dict]:
    if out.exists():
        raise ValueError("output directory must not exist")
    if not (1 <= max_files <= MAX_BATCH):
        raise ValueError("max_files out of bounds")
    if not (1 <= max_total_bytes <= MAX_SESSION_BYTES):
        raise ValueError("max_total_bytes out of bounds")
    if not (1 <= refresh_days <= 90):
        raise ValueError("refresh_days out of bounds")
    if forced_id is not None and not ID_PATTERN.fullmatch(forced_id):
        raise ValueError("invalid probe Drive ID")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now requires timezone")
    checkpoint = read_checkpoint(previous)
    entries = enumerator(folder_url)
    if not entries:
        raise ValueError("empty public folder listing; refusing to publish empty state")
    previous_items = dict(checkpoint["items"])
    previous_failures = dict(checkpoint.get("failures", {}))
    due, skipped = make_queue(entries, previous_items, now, refresh_days,
                              forced_id, set(previous_failures))
    cooling, eligible = [], []
    for item in due:
        retry_at = (None if forced_id else oversized_retry_after(
            previous_failures.get(item["id"]), item, now, refresh_days))
        if retry_at:
            cooling.append({"id": item["id"], "path": item["path"],
                            "reason": "oversize_retry_cooldown",
                            "retry_after": retry_at})
        else:
            eligible.append(item)
    due = eligible
    if git_tree is None:
        git_tree = subprocess.run(
            ["git", "ls-tree", "-r", "-z", "HEAD"],
            check=True, stdout=subprocess.PIPE,
        ).stdout
    out.mkdir(parents=True)
    report = {
        "schema": REPORT_SCHEMA, "scanned_at": now.isoformat(),
        "folder": folder_url, "listed_files": len(entries),
        "listed_files_independently_verified": False,
        "previously_verified_skipped": len(skipped),
        "queued_before_batch": len(due),
        "processed": [], "errors": [], "deferred": [],
        "retry_cooldown": cooling,
        "downloaded_bytes": 0,
        "published_source_bytes": 0,
        "automatic_integration_decisions": 0,
        "automatic_publication_authorized": False,
        "archive_deletion_authorized": False,
        "release_gate_credit": 0,
    }
    for item in due:
        if len(report["processed"]) + len(report["errors"]) >= max_files:
            report["deferred"].append({"id": item["id"], "path": item["path"],
                                       "reason": "batch_file_limit"})
            continue
        if report["downloaded_bytes"] >= max_total_bytes:
            report["deferred"].append({"id": item["id"], "path": item["path"],
                                       "reason": "batch_byte_limit"})
            continue
        try:
            result = downloader(item, out, git_tree, stage=False)
            if result["bytes"] > max_total_bytes - report["downloaded_bytes"]:
                report["deferred"].append({"id": item["id"], "path": item["path"],
                                           "reason": "batch_byte_limit_after_download",
                                           "bytes": result["bytes"]})
                continue
            report["processed"].append(result)
            previous_failures.pop(item["id"], None)
            report["downloaded_bytes"] += result["bytes"]
            zip_info = result.get("zip") or {}
            crosswalk = zip_info.get("crosswalk") or {}
            previous_items[item["id"]] = {
                "path": item["path"], "sha256": result["sha256"],
                "bytes": result["bytes"], "audited_at": now.isoformat(),
                "zip": result.get("zip") is not None,
                "source_like_members": crosswalk.get("source_like_members", 0),
                "exact_blob_occurrences": crosswalk.get("exact_blob_occurrences", 0),
                "unmatched_or_unexamined": crosswalk.get("unmatched_or_unexamined", 0),
                "nested_archives_encountered": crosswalk.get("nested_archives_encountered", 0),
                # Bounded metadata only, durable across later no-download cycles.
                "review_leads": zip_info.get("review_leads", []),
                "review_leads_filtered_or_truncated": zip_info.get(
                    "review_leads_filtered_or_truncated", 0),
            }
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            report["errors"].append({"id": item["id"], "path": item["path"],
                                     "error": str(exc)[:320]})
            previous_failures[item["id"]] = {"path": item["path"],
                                             "last_attempt": now.isoformat(),
                                             "error": str(exc)[:320]}
    new_checkpoint = {
        "schema": SCHEMA, "saved_at": now.isoformat(), "items": previous_items,
        "failures": previous_failures,
    }
    report["remaining_due"] = (len(report["deferred"]) + len(report["errors"])
                               + len(cooling))
    report["verified_total"] = len(previous_items)
    report["absent_from_current_listing"] = sorted(
        set(previous_items) - {item["id"] for item in entries}
    )
    # A review queue is an advisory, not a publishability determination.
    queue = {
        "schema": "ur-vault-integration-candidates/1",
        "generated_at": now.isoformat(),
        "needs_first_audit": [
            {"id": item["id"], "path": item["path"], "reason": item["reason"]}
            for item in due if item["id"] not in previous_items
        ],
        "needs_engineering_review": [
            {"id": id_, **fields, "rights_and_publication_review_required": True}
            for id_, fields in sorted(previous_items.items())
            if id_ in {item["id"] for item in entries}
            and fields.get("unmatched_or_unexamined", 0) > 0
        ],
        "download_errors": report["errors"],
        "retry_cooldown": cooling,
        "automatic_publication_authorized": False,
    }
    (out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "checkpoint.json").write_text(
        json.dumps(new_checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "queue.json").write_text(
        json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report, queue


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder-url", default=DEFAULT_FOLDER)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--max-files", type=int, default=3)
    parser.add_argument("--max-total-mib", type=int, default=64)
    parser.add_argument("--refresh-days", type=int, default=14)
    parser.add_argument("--file-id", help="One exact Drive ID; also rechecks recently audited items")
    args = parser.parse_args()
    try:
        report, queue = run_cycle(
            out=args.out, folder_url=args.folder_url, previous=args.previous,
            max_files=args.max_files, max_total_bytes=args.max_total_mib * 1024 * 1024,
            refresh_days=args.refresh_days, forced_id=args.file_id,
        )
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))
    print(
        f"Vault scheduled intake: listed={report['listed_files']} "
        f"downloaded={len(report['processed'])} "
        f"bytes={report['downloaded_bytes']} "
        f"skipped={report['previously_verified_skipped']} "
        f"pending={report['remaining_due']} "
        f"review_leads={len(queue['needs_engineering_review'])} "
        f"errors={len(report['errors'])} "
        f"cooldown={len(report['retry_cooldown'])}"
    )
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
