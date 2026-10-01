#!/usr/bin/env python3
"""Verify classification and byte integrity of reference/imported/.

The imported tree is an evidence corpus. This check prevents silent edits,
normalization, executable-bit drift, and unclassified additions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
IMPORTED = ROOT / "references" / "imported"
MANIFEST = IMPORTED / "MANIFEST.json"
ALLOWED_REVIEW_STATUS = {
    "audited-reference",
    "audited-known-defects",
    "archive-only-never-execute",
    "reference-only",
    "analyzed-reference",
    "unverified-leads",
    "immutable-input-corpus",
    "preservation-only",
}


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def tracked_imports() -> dict[str, str]:
    out = subprocess.check_output(
        ["git", "ls-files", "--stage", "reference/imported"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    result: dict[str, str] = {}
    for line in out.splitlines():
        if not line:
            continue
        meta, path = line.split("\t", 1)
        mode = meta.split()[0]
        result[path.replace("\\", "/")] = mode
    return result


def load_manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported imported-artifact manifest schema")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")
    return data


def verify() -> list[str]:
    manifest = load_manifest()
    failures: list[str] = []
    tracked = tracked_imports()
    tracked.pop("reference/imported/MANIFEST.json", None)

    entries: dict[str, dict] = {}
    for entry in manifest["entries"]:
        path = entry.get("path")
        if not isinstance(path, str) or not path.startswith("reference/imported/"):
            failures.append(f"invalid manifest path: {path!r}")
            continue
        if path == "reference/imported/MANIFEST.json":
            failures.append("manifest must not recursively classify itself")
            continue
        if path in entries:
            failures.append(f"duplicate manifest entry: {path}")
            continue
        entries[path] = entry

    missing_classification = sorted(set(tracked) - set(entries))
    stale_entries = sorted(set(entries) - set(tracked))
    for path in missing_classification:
        failures.append(f"unclassified imported artifact: {path}")
    for path in stale_entries:
        failures.append(f"manifest entry is not tracked: {path}")

    for path in sorted(set(tracked) & set(entries)):
        entry = entries[path]
        mode = tracked[path]
        if mode != "100644":
            failures.append(
                f"{path}: imported evidence must not be executable/symlinked; git mode is {mode}"
            )

        category = entry.get("category")
        if not isinstance(category, str) or not category:
            failures.append(f"{path}: missing category")
        review_status = entry.get("review_status")
        if review_status not in ALLOWED_REVIEW_STATUS:
            failures.append(f"{path}: invalid or missing review_status {review_status!r}")
        if path.lower().endswith(".exe") and review_status != "archive-only-never-execute":
            failures.append(f"{path}: historical executable must be archive-only-never-execute")
        if category == "bot-source" and review_status != "audited-known-defects":
            failures.append(f"{path}: imported bot source must carry audited-known-defects status")

        disk = ROOT / path
        data = disk.read_bytes()
        expected_size = entry.get("size")
        if expected_size != len(data):
            failures.append(f"{path}: size {len(data)} != manifest {expected_size}")

        actual_blob = git_blob_sha1(data)
        expected_blob = entry.get("git_blob_sha1")
        if actual_blob != expected_blob:
            failures.append(
                f"{path}: git blob {actual_blob} != preservation pin {expected_blob}"
            )

        upstream_blob = entry.get("upstream_git_blob_sha1")
        if upstream_blob is not None and actual_blob != upstream_blob:
            failures.append(
                f"{path}: local blob {actual_blob} != recorded upstream blob {upstream_blob}"
            )

        external_sha256 = entry.get("external_sha256")
        if external_sha256 is not None:
            actual_sha256 = hashlib.sha256(data).hexdigest()
            if actual_sha256 != external_sha256:
                failures.append(
                    f"{path}: sha256 {actual_sha256} != source hash {external_sha256}"
                )

    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Imported-reference audit failed:")
        for failure in failures:
            print(f"  {failure}")
        return 1

    manifest = load_manifest()
    categories: dict[str, int] = {}
    for entry in manifest["entries"]:
        categories[entry["category"]] = categories.get(entry["category"], 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(categories.items()))
    print(f"Imported-reference audit passed ({len(manifest['entries'])} artifacts; {summary}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
