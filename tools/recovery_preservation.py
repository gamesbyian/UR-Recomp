#!/usr/bin/env python3
"""Lossless, bounded recovery ZIP staging before a fragile publication attempt.

Offline only. This tool never uploads to Drive, publishes to GitHub or retries a
denied write. Its readback mode verifies downloaded bytes, not Drive permissions.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

if __package__:
    from .strict_vault_manifest import verify as verify_zip
else:
    from strict_vault_manifest import verify as verify_zip

HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[a-z0-9][a-z0-9-]{2,95}\Z")
WORK = re.compile(r"UR-[A-Z0-9-]+\Z")
BLOCKED_PARTS = {".git", ".ssh", ".aws", "secrets", "credentials", "roms"}
BLOCKED_SUFFIXES = {".sfc", ".smc", ".nes", ".gb", ".gbc", ".gba", ".key", ".pem"}
MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 48 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    parts = name.split("/")
    if (not name or path.is_absolute() or path.as_posix() != name
            or "\\" in name or ":" in name
            or any(part in ("", ".", "..") or part.endswith((".", " "))
                   for part in parts)
            or any(ord(ch) < 32 for ch in name)
            or any(part.lower() in BLOCKED_PARTS for part in parts)
            or path.suffix.lower() in BLOCKED_SUFFIXES
            or path.name.lower().startswith(".env")):
        raise ValueError("unsafe or sensitive source path: " + name)
    return path


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def zip_info(name):
    info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def stage(root, paths, out, candidate_id, work_id, source_main_sha):
    if not ID.fullmatch(candidate_id) or not WORK.fullmatch(work_id):
        raise ValueError("invalid candidate/work ID")
    if not HEX40.fullmatch(source_main_sha):
        raise ValueError("source_main_sha must be exact lowercase 40-hex")
    if not paths or len(set(paths)) != len(paths):
        raise ValueError("provide distinct file paths")
    root = Path(root).resolve(strict=True)
    out = Path(out)
    if out.exists():
        raise ValueError("refusing to overwrite an existing archive")
    payload = {}
    total = 0
    for name in paths:
        relative = safe_name(name)
        source = root / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError("missing, nonregular or symlinked file: " + name)
        if not source.resolve(strict=True).is_relative_to(root):
            raise ValueError("file escapes stage root: " + name)
        size = source.stat().st_size
        if size > MAX_FILE or total + size > MAX_TOTAL:
            raise ValueError("source exceeds bounded recovery limits")
        raw = source.read_bytes()
        if len(raw) != size:
            raise ValueError("source changed during staging")
        payload["payload/" + name] = raw
        total += size
    handoff = {
        "schema": "ur-preservation-handoff/1",
        "candidate_id": candidate_id,
        "work_id": work_id,
        "source_main_sha": source_main_sha,
        "paths": sorted(paths),
        "github_outcome": "not_yet_recorded",
        "drive_outcome": "not_yet_recorded",
        "release_gate_credit": False,
    }
    payload["handoff.json"] = canonical(handoff)
    manifest = {name: {"bytes": len(raw), "sha256": digest(raw)}
                for name, raw in sorted(payload.items())}
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ZipFile(out, "x") as archive:
            for name, raw in sorted(payload.items()):
                archive.writestr(zip_info(name), raw)
            archive.writestr(zip_info("MANIFEST.json"), canonical(manifest))
        raw_zip = out.read_bytes()
        evidence = verify_zip(raw_zip, expected_sha256=digest(raw_zip))
    except BaseException:
        out.unlink(missing_ok=True)
        raise
    return {"archive": str(out), "candidate_id": candidate_id,
            "archive_sha256": digest(raw_zip), "bytes": len(raw_zip),
            "payloads": evidence["manifested_payloads"],
            "remote_preserved": False, "release_gate_credit": False}


def audit(original, downloaded, expected_sha256):
    if not HEX64.fullmatch(expected_sha256):
        raise ValueError("provide exact expected staged ZIP SHA-256")
    original = Path(original).read_bytes()
    if digest(original) != expected_sha256:
        raise ValueError("original archive differs from staged SHA")
    verified = verify_zip(original, expected_sha256=expected_sha256)
    downloaded = Path(downloaded).read_bytes()
    if digest(downloaded) != expected_sha256 or downloaded != original:
        raise ValueError("downloaded archive is not byte-identical")
    verify_zip(downloaded, expected_sha256=expected_sha256)
    return {"archive_sha256": expected_sha256,
            "manifested_payloads": verified["manifested_payloads"],
            "downloaded_bytes_equal": True,
            "provider_drive_id_independently_verified": False,
            "release_gate_credit": False}


def validate_incidents(document):
    """Fail closed on invented acceptance or unverified remote recovery."""
    if (type(document) is not dict or
            document.get("schema") != "ur-publication-incidents/1" or
            document.get("scope") != "curated_not_exhaustive" or
            type(document.get("incidents")) is not list):
        raise ValueError("unknown incident register schema or scope")
    seen = set()
    for entry in document["incidents"]:
        needed = {"incident_id", "work_id", "candidate_id", "source_main_sha",
                  "operation", "target_path", "original_error", "classification",
                  "vault_file_id", "vault_sha256", "byte_readback", "disposition",
                  "next_authorized_action", "release_gate_credit"}
        if type(entry) is not dict or not needed.issubset(entry):
            raise ValueError("incomplete publication incident")
        inc = entry["incident_id"]
        if not isinstance(inc, str) or not ID.fullmatch(inc) or inc in seen:
            raise ValueError("invalid/duplicate publication incident ID")
        seen.add(inc)
        if not isinstance(entry["work_id"], str) or not WORK.fullmatch(entry["work_id"]):
            raise ValueError("invalid work ID")
        if not isinstance(entry["original_error"], str) or not entry["original_error"].strip():
            raise ValueError("incident must preserve exact raw error")
        if entry["classification"] not in {
                "explicit_safety_denial", "technical_retryable", "source_conflict",
                "unknown", "resolved_in_main"}:
            raise ValueError("invalid failure classification")
        if entry["byte_readback"] not in {"pending", "failed", "verified", "unavailable"}:
            raise ValueError("invalid byte readback claim")
        sha = entry["vault_sha256"]
        if sha is not None and (type(sha) is not str or not HEX64.fullmatch(sha)):
            raise ValueError("invalid archive hash")
        source = entry["source_main_sha"]
        if source is not None and (type(source) is not str or not HEX40.fullmatch(source)):
            raise ValueError("invalid source hash")
        if entry["byte_readback"] == "verified" and (
                sha is None or not isinstance(entry["vault_file_id"], str)
                or len(entry["vault_file_id"]) < 15):
            raise ValueError("cannot claim verified readback without ID and outer SHA")
        if entry["release_gate_credit"] is not False:
            raise ValueError("incident cannot award release credit")
        if not isinstance(entry["next_authorized_action"], str) or not entry["next_authorized_action"].strip():
            raise ValueError("missing independent next action")
    return {"incidents_validated": len(seen), "release_gate_credit": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    create = sub.add_parser("stage", help="stage bounded immutable source package")
    create.add_argument("--root", required=True)
    create.add_argument("--out", required=True)
    create.add_argument("--candidate-id", required=True)
    create.add_argument("--work-id", required=True)
    create.add_argument("--source-main-sha", required=True)
    create.add_argument("--file", action="append", required=True)
    check = sub.add_parser("readback", help="compare actual downloaded ZIP to staged bytes")
    check.add_argument("--original", required=True)
    check.add_argument("--downloaded", required=True)
    check.add_argument("--expected-sha256", required=True)
    incidents = sub.add_parser("check-incidents", help="validate exact-error incident register")
    incidents.add_argument("--registry", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "stage":
            result = stage(args.root, args.file, args.out, args.candidate_id,
                           args.work_id, args.source_main_sha)
        elif args.action == "readback":
            result = audit(args.original, args.downloaded, args.expected_sha256)
        else:
            result = validate_incidents(json.loads(Path(args.registry).read_text(encoding="utf-8")))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
