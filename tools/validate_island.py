#!/usr/bin/env python3
"""Validate UR-Recomp's repository-owned third-party/island manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ISLAND = ROOT / "third_party" / "manifest.json"
TOOLCHAIN = ROOT / "tools" / "toolchain.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_sha256(root: Path) -> str:
    """Hash relative paths + bytes, excluding VCS/build residue."""
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root)
        if any(part in {".git", "__pycache__"} for part in rel.parts):
            continue
        h.update(str(rel).replace("\\", "/").encode("utf-8"))
        h.update(b"\0")
        h.update(file_sha256(path).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    island = load(ISLAND)
    toolchain = load(TOOLCHAIN)

    if island.get("schema_version") != 1:
        errors.append("third_party/manifest.json: schema_version must be 1")
    components = island.get("components")
    if not isinstance(components, list):
        return ["third_party/manifest.json: components must be a list"], notes

    tool_by_id = {t.get("id"): t for t in toolchain.get("tools", []) if isinstance(t, dict)}
    seen: set[str] = set()

    for i, comp in enumerate(components):
        if not isinstance(comp, dict):
            errors.append(f"component {i}: must be an object")
            continue
        cid = comp.get("id")
        if not isinstance(cid, str) or not ID.fullmatch(cid):
            errors.append(f"component {i}: invalid id {cid!r}")
            continue
        if cid in seen:
            errors.append(f"{cid}: duplicate component")
        seen.add(cid)

        mode = comp.get("mode")
        if mode not in {"pending", "vendored", "archive", "optional-external"}:
            errors.append(f"{cid}: invalid mode {mode!r}")

        upstream = comp.get("upstream_url")
        revision = comp.get("revision")
        if not isinstance(upstream, str) or not upstream.startswith("https://github.com/"):
            errors.append(f"{cid}: upstream_url must be an https://github.com URL")
        if not isinstance(revision, str) or not HEX40.fullmatch(revision):
            errors.append(f"{cid}: revision must be a full lowercase commit SHA")

        tool = tool_by_id.get(cid)
        if tool:
            if tool.get("url") != upstream:
                errors.append(f"{cid}: upstream_url diverges from tools/toolchain.json")
            if tool.get("revision") != revision:
                errors.append(f"{cid}: revision diverges from tools/toolchain.json")

        source_path = comp.get("source_path")
        archive_path = comp.get("archive_path")
        digest = comp.get("source_sha256")
        license_spdx = comp.get("license_spdx")
        license_path = comp.get("license_path")

        if mode == "pending":
            if source_path or archive_path or digest:
                errors.append(f"{cid}: pending component must not claim a local source/archive/hash")
            notes.append(f"{cid}: pending")
            continue

        if mode == "optional-external":
            notes.append(f"{cid}: optional external/manual")
            continue

        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            errors.append(f"{cid}: islanded component needs source_sha256")
        if not isinstance(license_spdx, str) or not license_spdx:
            errors.append(f"{cid}: islanded component needs license_spdx")
        if not isinstance(license_path, str) or not license_path:
            errors.append(f"{cid}: islanded component needs license_path")
        else:
            lp = ROOT / license_path
            if not lp.is_file():
                errors.append(f"{cid}: missing license file {license_path}")

        if mode == "vendored":
            if not isinstance(source_path, str) or not source_path:
                errors.append(f"{cid}: vendored component needs source_path")
                continue
            src = ROOT / source_path
            if not src.is_dir():
                errors.append(f"{cid}: missing source directory {source_path}")
            elif isinstance(digest, str) and HEX64.fullmatch(digest):
                actual = tree_sha256(src)
                if actual != digest:
                    errors.append(f"{cid}: source tree hash drift {actual} != {digest}")
        elif mode == "archive":
            if not isinstance(archive_path, str) or not archive_path:
                errors.append(f"{cid}: archive component needs archive_path")
                continue
            ap = ROOT / archive_path
            if not ap.is_file():
                errors.append(f"{cid}: missing archive {archive_path}")
            elif isinstance(digest, str) and HEX64.fullmatch(digest):
                actual = file_sha256(ap)
                if actual != digest:
                    errors.append(f"{cid}: archive hash drift {actual} != {digest}")

    return errors, notes


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--status", action="store_true", help="print component migration status")
    args = p.parse_args()
    errors, notes = validate()
    if args.status:
        for note in notes:
            print(note)
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1
    print(f"island manifest valid ({len(notes)} classified components)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
