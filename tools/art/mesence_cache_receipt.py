#!/usr/bin/env python3
"""Bounded source/patch/byte integrity receipt for the pinned Linux MesenCE cache.

This is a self-hash, not a digital signature or substitute for a trusted
default-branch producer. It never reads, stores or uploads the game ROM.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat

SCHEMA = "ur-mesence-linux-source-cache/1"
RECEIPT = "mesence-cache-receipt.json"
SHA1 = re.compile(r"[a-f0-9]{40}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
MAX_FILES = 5000
MAX_TOTAL_BYTES = 1024 * 1024 * 1024


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_json(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("ascii")).hexdigest()


def snapshot(cache: Path) -> dict:
    if not cache.is_dir() or cache.is_symlink():
        raise ValueError("missing or redirected MesenCE cache directory")
    manifest: dict[str, dict] = {}
    total = 0
    for path in sorted(cache.rglob("*")):
        name = path.relative_to(cache).as_posix()
        if name == RECEIPT:
            continue
        if path.is_symlink():
            target = os.readlink(path)
            try:
                path.resolve(strict=True).relative_to(cache.resolve())
            except (ValueError, OSError) as exc:
                raise ValueError("redirected MesenCE cached dependency") from exc
            manifest[name] = {"kind": "link", "target": target}
        elif path.is_dir():
            continue
        elif path.is_file():
            info = path.stat()
            if not stat.S_ISREG(info.st_mode) or info.st_size <= 0:
                raise ValueError("invalid MesenCE cached file")
            total += info.st_size
            if total > MAX_TOTAL_BYTES:
                raise ValueError("oversized MesenCE cache")
            manifest[name] = {"kind": "file", "size": info.st_size,
                              "sha256": digest_file(path),
                              "executable": bool(info.st_mode & stat.S_IXUSR)}
        else:
            raise ValueError("unsupported MesenCE cache member")
        if len(manifest) > MAX_FILES:
            raise ValueError("too many MesenCE cache members")
    binary = cache / "Mesen"
    if ("Mesen" not in manifest or manifest["Mesen"]["kind"] != "file"
            or not os.access(binary, os.X_OK)):
        raise ValueError("missing executable MesenCE guest")
    with binary.open("rb") as stream:
        if stream.read(4) != b"\x7fELF":
            raise ValueError("MesenCE guest lacks ELF identity")
    return manifest


def bound_record(cache: Path, revision: str, patch: Path) -> dict:
    if not SHA1.fullmatch(revision) or not patch.is_file() or patch.is_symlink():
        raise ValueError("invalid pinned source revision or patch")
    return {"schema": SCHEMA, "source_revision": revision,
            "input_patch_sha256": digest_file(patch),
            "files": snapshot(cache)}


def seal(cache: Path, revision: str, patch: Path) -> str:
    record = bound_record(cache, revision, patch)
    record["receipt_sha256"] = digest_json(record)
    receipt = cache / RECEIPT
    with receipt.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return record["receipt_sha256"]


def verify(cache: Path, revision: str, patch: Path) -> str:
    receipt = cache / RECEIPT
    if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size > 750000:
        raise ValueError("missing or oversized MesenCE cache receipt")
    try:
        original = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError("unreadable MesenCE cache receipt") from exc
    if not isinstance(original, dict) or not isinstance(original.get("receipt_sha256"), str):
        raise ValueError("invalid MesenCE cache receipt")
    actual = original["receipt_sha256"]
    unsigned = {k: v for k, v in original.items() if k != "receipt_sha256"}
    if not SHA256.fullmatch(actual) or digest_json(unsigned) != actual:
        raise ValueError("MesenCE cache receipt digest mismatch")
    if unsigned != bound_record(cache, revision, patch):
        raise ValueError("MesenCE cached bytes or pinned source inputs differ")
    return actual


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("seal", "verify"))
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--patch", type=Path, required=True)
    args = parser.parse_args()
    digest = (seal if args.mode == "seal" else verify)(args.cache, args.revision, args.patch)
    print(f"MESENCE_CACHE_{args.mode.upper()}=passed receipt_sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
