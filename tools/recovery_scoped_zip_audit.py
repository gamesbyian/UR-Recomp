#!/usr/bin/env python3
"""Inspect one selected ZIP nesting path with bounded verified reads.

This is intentionally NOT a full archive auditor. Only selected nested ZIP
members are CRC-checked and read. Other payloads remain unexamined. This tool
does not extract, execute, stage or publish archive contents, and cannot grant
release, publication, or integration credit.
"""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import stat
from zipfile import BadZipFile, ZipFile

MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_SELECTED_MEMBER_BYTES = 32 * 1024 * 1024
MAX_READ_BYTES = 64 * 1024 * 1024
MAX_DEPTH = 4
MAX_MEMBERS = 10000


def validate_zip_members(archive: ZipFile) -> dict:
    """Validate directory metadata, but do not decompress unselected members."""
    names, expanded = set(), 0
    infos = archive.infolist()
    if not infos or len(infos) > MAX_MEMBERS:
        raise ValueError("empty or oversized ZIP directory")
    for info in infos:
        name = info.filename
        if (not name or name.startswith("/") or "\\" in name or "\x00" in name
                or any(part in ("", ".", "..") for part in name.split("/"))
                or info.is_dir() or info.flag_bits & 1
                or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)):
            raise ValueError("unsafe ZIP member")
        folded = name.casefold()
        if folded in names:
            raise ValueError("duplicate/aliased ZIP member")
        names.add(folded)
        expanded += info.file_size
    for folded in names:
        parts = folded.split("/")
        if any("/".join(parts[:i]) in names for i in range(1, len(parts))):
            raise ValueError("ZIP file/directory prefix collision")
    return {"members_declared": len(infos),
            "expanded_declared_bytes": expanded,
            "member_contents_all_verified": False}


def inspect(raw: bytes, selected: list[str], leaf: str | None = None) -> dict:
    if len(raw) > MAX_ARCHIVE_BYTES or not raw:
        raise ValueError("outer ZIP exceeds input budget")
    if len(selected) > MAX_DEPTH:
        raise ValueError("selected archive nesting depth exceeded")
    report = {"schema": "ur-scoped-nested-zip-audit/1",
              "outer_sha256": hashlib.sha256(raw).hexdigest(),
              "selected_members": [], "layers": [],
              "all_unselected_member_contents_verified": False,
              "full_archive_crosswalk_qualified": False,
              "source_publication_authorized": False,
              "release_gate_credit": 0}
    bytes_read = 0
    archive_bytes = raw
    for depth in range(len(selected) + 1):
        try:
            with ZipFile(BytesIO(archive_bytes)) as archive:
                layer = validate_zip_members(archive)
                layer["depth"] = depth
                layer["archive_sha256"] = hashlib.sha256(archive_bytes).hexdigest()
                report["layers"].append(layer)
                if depth == len(selected):
                    if leaf is not None:
                        if leaf not in archive.namelist():
                            raise ValueError("selected leaf member missing")
                        info = archive.getinfo(leaf)
                        if info.file_size > MAX_SELECTED_MEMBER_BYTES or (
                                bytes_read + info.file_size > MAX_READ_BYTES):
                            raise ValueError("selected leaf member exceeds read budget")
                        payload = archive.read(info)
                        bytes_read += len(payload)
                        git_hash = hashlib.sha1(
                            b"blob " + str(len(payload)).encode() + b"\0" + payload
                        ).hexdigest()
                        report["leaf_member"] = {
                            "name": leaf, "bytes": len(payload),
                            "sha256": hashlib.sha256(payload).hexdigest(),
                            "git_blob_sha": git_hash, "crc_verified": True}
                    break
                name = selected[depth]
                if name not in archive.namelist() or not name.lower().endswith(".zip"):
                    raise ValueError("selected nested ZIP member missing")
                info = archive.getinfo(name)
                if info.file_size > MAX_SELECTED_MEMBER_BYTES or (
                        bytes_read + info.file_size > MAX_READ_BYTES):
                    raise ValueError("selected ZIP member exceeds read budget")
                payload = archive.read(info)
                bytes_read += len(payload)
                report["selected_members"].append({
                    "name": name, "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "crc_verified": True})
                archive_bytes = payload
        except BadZipFile as exc:
            raise ValueError("corrupt selected ZIP structure or CRC") from exc
    report["selected_nested_bytes_read"] = bytes_read
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--member", action="append", default=[],
                        help="Exact nested ZIP member name for each successive level")
    parser.add_argument("--leaf", help="Exact member to hash/CRC-check without extracting")
    parser.add_argument("--expected-sha256", help="Optional exact outer SHA-256 pin")
    args = parser.parse_args()
    if args.archive.stat().st_size > MAX_ARCHIVE_BYTES:
        parser.error("outer ZIP exceeds input budget")
    blob = args.archive.read_bytes()
    if args.expected_sha256 and hashlib.sha256(blob).hexdigest() != args.expected_sha256:
        parser.error("outer SHA-256 differs from expected pin")
    try:
        result = inspect(blob, args.member, args.leaf)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
