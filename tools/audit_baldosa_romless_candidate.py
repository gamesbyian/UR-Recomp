#!/usr/bin/env python3
"""Independently inspect a ROM-free Baldosa Windows ZIP before extraction.

No ROM, Win32 process or imported guest is needed. This checks archive
structure, bounded members, canonical manifest, every member's SHA-256 and
the claimed source revision. A self-contained manifest is NOT a signature:
release QA must additionally pin the ZIP digest from an independent receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

from assemble_baldosa_windows_candidate import (
    EXE, LAUNCHER, MANIFEST, MAX_EXE_BYTES, PREFIX, README, ROM,
    USA_SHA256, ZIP_EPOCH,
)

FORMAT = "ur-recomp-baldosa-windows-x64-romless-candidate-v1"
STATUS = "native-modern-root-stock-1p-2p-candidate-only"
MAX_SMALL_BYTES = 256 * 1024
MAX_ZIP_BYTES = MAX_EXE_BYTES + 8 * MAX_SMALL_BYTES
CHUNK = 1 << 20
IMMUTABLE = sorted((EXE, LAUNCHER, README))
ALL_MEMBERS = sorted((*IMMUTABLE, MANIFEST))


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("ROMLESS_CANDIDATE_INVALID: " + reason)


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(archive: Path, *, expected_revision: str | None = None,
            expected_zip_sha256: str | None = None) -> dict[str, object]:
    """Return source/ZIP/EXE hashes only after all members have been checked."""
    require(archive.is_file() and not archive.is_symlink(),
            "archive absent or redirected")
    require(0 < archive.stat().st_size <= MAX_ZIP_BYTES,
            "archive outside bounded size")
    zip_sha256 = file_digest(archive)
    if expected_zip_sha256 is not None:
        require(re.fullmatch(r"[0-9a-f]{64}", expected_zip_sha256) is not None,
                "expected ZIP SHA-256 must be lowercase hex")
        require(zip_sha256 == expected_zip_sha256,
                "ZIP differs from independently pinned SHA-256")
    if expected_revision is not None:
        require(isinstance(expected_revision, str) and expected_revision and
                len(expected_revision) <= 100 and
                all(33 <= ord(c) <= 126 for c in expected_revision),
                "expected source revision is not canonical")

    with zipfile.ZipFile(archive, "r") as z:
        infos = z.infolist()
        require([i.filename for i in infos] ==
                [PREFIX + name for name in ALL_MEMBERS],
                "ZIP members are missing, duplicated, extra or out of order")
        for info, name in zip(infos, ALL_MEMBERS):
            maximum = MAX_EXE_BYTES if name == EXE else MAX_SMALL_BYTES
            require(not info.is_dir() and not (info.flag_bits & 1),
                    "directory/encrypted member not permitted")
            mode = stat.S_IFMT(info.external_attr >> 16)
            require(mode in (0, stat.S_IFREG), "non-regular ZIP member")
            require(info.compress_type == zipfile.ZIP_DEFLATED,
                    "unexpected compression method")
            require(info.date_time == ZIP_EPOCH,
                    "non-reproducible member timestamp")
            require(0 <= info.file_size <= maximum,
                    "member exceeds published size budget")

        manifest_bytes = z.read(PREFIX + MANIFEST, MAX_SMALL_BYTES + 1)
        require(len(manifest_bytes) <= MAX_SMALL_BYTES,
                "manifest decompression exceeds budget")
        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("ROMLESS_CANDIDATE_INVALID: invalid manifest JSON") from exc
        require(isinstance(manifest, dict) and
                set(manifest) == {
                    "format", "project_revision", "immutable_files",
                    "rom_bundled", "rom_filename", "rom_sha256_required",
                    "profile_data_bundled", "status",
                }, "manifest schema differs from published contract")
        require(manifest_bytes == (
            json.dumps(manifest, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8"), "manifest JSON is not canonical")
        revision = manifest["project_revision"]
        require(isinstance(revision, str) and 0 < len(revision) <= 100 and
                all(33 <= ord(c) <= 126 for c in revision),
                "manifest source revision is not canonical")
        require(expected_revision is None or revision == expected_revision,
                "manifest revision differs from checked-out source")
        require(manifest["format"] == FORMAT and manifest["status"] == STATUS and
                manifest["rom_bundled"] is False and
                manifest["profile_data_bundled"] is False and
                manifest["rom_filename"] == ROM and
                manifest["rom_sha256_required"] == USA_SHA256,
                "ROM-free identity or distribution status changed")

        entries = manifest["immutable_files"]
        require(isinstance(entries, list) and len(entries) == len(IMMUTABLE),
                "manifest must enumerate three immutable members")
        result: dict[str, str] = {}
        for entry, name in zip(entries, IMMUTABLE):
            require(isinstance(entry, dict) and
                    set(entry) == {"path", "bytes", "sha256"} and
                    entry["path"] == name and
                    type(entry["bytes"]) is int and
                    0 <= entry["bytes"] <= (
                        MAX_EXE_BYTES if name == EXE else MAX_SMALL_BYTES) and
                    isinstance(entry["sha256"], str) and
                    re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is not None,
                    "malformed or reordered immutable member entry")
            actual_size = 0
            hasher = hashlib.sha256()
            maximum = MAX_EXE_BYTES if name == EXE else MAX_SMALL_BYTES
            with z.open(PREFIX + name) as source:
                for chunk in iter(lambda: source.read(CHUNK), b""):
                    actual_size += len(chunk)
                    require(actual_size <= maximum,
                            "decompressed member exceeds budget")
                    hasher.update(chunk)
            require(actual_size == entry["bytes"] and
                    actual_size == z.getinfo(PREFIX + name).file_size and
                    hasher.hexdigest() == entry["sha256"],
                    "member bytes differ from immutable manifest: " + name)
            result[name] = hasher.hexdigest()

        readme_bytes = z.read(PREFIX + README, MAX_SMALL_BYTES + 1)
        require(readme_bytes.endswith(
            ("Project source revision: " + revision + "\n").encode("ascii")),
            "README source identity differs from manifest")

    return {
        "source_revision": revision,
        "zip_sha256": zip_sha256,
        "exe_sha256": result[EXE],
        "launcher_sha256": result[LAUNCHER],
        "readme_sha256": result[README],
        "all_immutable_members_verified": True,
        "rom_bundled": False,
        "profile_data_bundled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--expected-revision")
    parser.add_argument("--expected-zip-sha256")
    args = parser.parse_args()
    print(json.dumps(inspect(
        args.zip, expected_revision=args.expected_revision,
        expected_zip_sha256=args.expected_zip_sha256,
    ), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
