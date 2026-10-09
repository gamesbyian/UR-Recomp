#!/usr/bin/env python3
"""Fail-closed audit of the pinned baldosa repo's entire Git-tree census.

The source census records every upstream path, including generated output we
intentionally do not duplicate. The ordinary imported-reference audit separately
verifies all imported file bytes and Git blob SHA-1 values.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "analysis/data/baldosa-upstream-file-census.json"
MANIFEST = ROOT / "reference/imported/MANIFEST.json"
PREFIX = "reference/imported/reverse-engineering/baldosa-uniracers-recomp/"
SOURCE_COMMIT = "10b864b9d14a7b7416dd909eb7b054c88faef101"
VALID_DISPOSITIONS = {
    "directory", "pinned-submodule", "imported-byte-identical",
    "metadata-only-generated", "metadata-only-pycache",
    "metadata-only-empty-placeholder",
}
EXTERNAL_GITLINKS = {
    "snesrecomp": "075fbe4c8e0d97b0013be541795c39cb644a9709",
    "recomp-ui": "7e884a227accea91ddb378671bd49aaeeea13371",
}


def validate(census: dict, manifest: dict) -> list[str]:
    errors: list[str] = []
    if census.get("schema_version") != 1 or census.get("pinned_commit") != SOURCE_COMMIT:
        errors.append("census version or pinned source commit changed")
    items = census.get("entries", [])
    if not isinstance(items, list):
        return errors + ["entries must be a list"]
    if len(items) != 210 or census.get("source_tree_entries") != 210:
        errors.append("upstream tree census must have exactly 210 entries")
    by_path: dict[str, dict] = {}
    for row in items:
        p = row.get("path", "")
        if not p or p in by_path:
            errors.append(f"missing or duplicate source path: {p!r}")
            continue
        by_path[p] = row
        if row.get("disposition") not in VALID_DISPOSITIONS:
            errors.append(f"bad disposition for {p}")
        if not row.get("role") or str(row["role"]).startswith("UNCLASSIFIED"):
            errors.append(f"unclassified role: {p}")
        if row.get("type") == "tree" and row.get("disposition") != "directory":
            errors.append(f"tree not directory: {p}")
        if row.get("type") == "commit" and row.get("disposition") != "pinned-submodule":
            errors.append(f"gitlink not pinned: {p}")
        if row.get("type") == "blob":
            if row.get("mode") not in {"100644", "100755"} or not isinstance(row.get("size"), int):
                errors.append(f"bad regular-file metadata: {p}")
            if row.get("disposition") == "metadata-only-generated" and not (
                p.startswith("src/gen/") or p == "recomp/funcs.h"
            ):
                errors.append(f"unclassified omission (generated): {p}")
            if row.get("disposition") == "metadata-only-pycache" and not p.startswith("tools/__pycache__/"):
                errors.append(f"unclassified omission (pycache): {p}")
            if row.get("disposition") == "metadata-only-empty-placeholder" and (
                not p.endswith("/.gitkeep") or row.get("size") != 0
            ):
                errors.append(f"unclassified omission (placeholder): {p}")
        parent = p.rpartition("/")[0]
        if parent and parent not in [r.get("path") for r in items if r.get("type") == "tree"]:
            errors.append(f"missing parent directory in Git tree: {p}")

    for path, sha in EXTERNAL_GITLINKS.items():
        obj = by_path.get(path)
        if not obj or obj.get("sha") != sha or obj.get("type") != "commit":
            errors.append(f"changed or missing external submodule {path}")

    entries = manifest.get("entries", [])
    imported = {str(e.get("path")): e for e in entries if str(e.get("path", "")).startswith(PREFIX)}
    census_imports = {
        PREFIX + p: row for p, row in by_path.items() if row.get("disposition") == "imported-byte-identical"
    }
    if set(census_imports) != set(imported):
        for p in sorted(set(census_imports) ^ set(imported)):
            errors.append(f"intake/census disagreement: {p}")
    for p, row in census_imports.items():
        e = imported.get(p, {})
        if row.get("sha") != e.get("git_blob_sha1") or row.get("sha") != e.get("upstream_git_blob_sha1"):
            errors.append(f"blob provenance mismatch: {p}")
        if row.get("size") != e.get("size"):
            errors.append(f"size mismatch: {p}")
    stats = Counter((r.get("type"), r.get("disposition")) for r in by_path.values())
    if (stats["tree", "directory"], stats["commit", "pinned-submodule"],
        stats["blob", "imported-byte-identical"]) != (22, 2, 85):
        errors.append("unexpected directory/gitlink/import count")
    other = sum(stats["blob", k] for k in (
        "metadata-only-generated", "metadata-only-pycache", "metadata-only-empty-placeholder"
    ))
    if other != 101:
        errors.append(f"expected 101 omitted bytecode/generated/placeholder blobs; got {other}")
    return errors


def main() -> int:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = validate(census, manifest)
    if errors:
        for err in errors:
            print("Baldosa-census ERROR:", err)
        return 1
    print("Baldosa census valid: 210 entries; 186 files, 22 dirs, 2 submodules; "
          "85 byte-identical imported sources, 101 deliberate metadata-only omissions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
