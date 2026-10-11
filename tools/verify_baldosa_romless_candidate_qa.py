#!/usr/bin/env python3
"""Independent, ROM-free admission for the provisional Baldosa Windows ZIP.

This reads a *prebuilt* four-member native candidate and requires the
reviewer's externally nominated full source SHA and actual ZIP digest.
It does not build, launch, download, extract ROM data, claim native 2P
Records acceptance, or authenticate the nomination itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from assemble_baldosa_windows_candidate import (
    EXE, LAUNCHER, README, MANIFEST, ROM, USA_SHA256, PREFIX,
    ZIP_EPOCH, MAX_EXE_BYTES, launcher, readme,
)
from evidence_contract import assertion, make_envelope

SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED = tuple(sorted((EXE, LAUNCHER, README, MANIFEST)))
PAYLOAD_NAMES = tuple(sorted((EXE, LAUNCHER, README)))
MAX_ZIP_BYTES = MAX_EXE_BYTES + 2 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024
MAX_LAUNCHER_BYTES = 32 * 1024
MAX_README_BYTES = 64 * 1024
BLOCK = 1 << 20


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(BLOCK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zip_member_digest(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest = hashlib.sha256()
    count = 0
    with archive.open(info) as stream:
        for chunk in iter(lambda: stream.read(BLOCK), b""):
            count += len(chunk)
            if count > info.file_size:
                raise ValueError("decompressed candidate payload exceeded advertised size")
            digest.update(chunk)
    if count != info.file_size:
        raise ValueError("candidate payload size mismatch after decompression")
    return digest.hexdigest()


def audit(archive_path: Path, source_sha: str, zip_sha256: str) -> dict:
    if not isinstance(source_sha, str) or not SHA40.fullmatch(source_sha):
        raise ValueError("Baldosa candidate needs nominated exact lowercase 40-hex commit")
    if not isinstance(zip_sha256, str) or not SHA256.fullmatch(zip_sha256):
        raise ValueError("Baldosa candidate needs nominated exact lowercase 64-hex ZIP digest")
    if archive_path.is_symlink() or not archive_path.is_file():
        raise ValueError("Baldosa candidate ZIP missing or symlink-backed")
    if archive_path.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("Baldosa candidate ZIP exceeds independent size budget")
    actual = file_digest(archive_path)
    if actual != zip_sha256:
        raise ValueError("Baldosa candidate ZIP differs from independently nominated digest")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            info = archive.infolist()
            names = [x.filename for x in info]
            if names != [PREFIX + x for x in EXPECTED]:
                raise ValueError("Baldosa candidate has extra, missing, duplicate or unordered members")
            for item in info:
                expected_limit = {
                    EXE: MAX_EXE_BYTES,
                    LAUNCHER: MAX_LAUNCHER_BYTES,
                    README: MAX_README_BYTES,
                    MANIFEST: MAX_MANIFEST_BYTES,
                }[item.filename.removeprefix(PREFIX)]
                if (item.is_dir() or item.file_size > expected_limit
                        or item.compress_type != zipfile.ZIP_DEFLATED
                        or item.date_time != ZIP_EPOCH
                        or item.external_attr != (0o100644 << 16)):
                    raise ValueError("Baldosa candidate contains noncanonical ZIP metadata")
            raw_manifest = archive.read(PREFIX + MANIFEST)
            try:
                metadata = json.loads(raw_manifest.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise ValueError("Baldosa candidate manifest malformed") from exc
            if (not isinstance(metadata, dict)
                    or raw_manifest != (json.dumps(metadata, sort_keys=True, indent=2) + "\n").encode("utf-8")):
                raise ValueError("Baldosa candidate manifest not canonical")
            expected_headers = {
                "format": "ur-recomp-baldosa-windows-x64-romless-candidate-v1",
                "project_revision": source_sha,
                "rom_bundled": False,
                "rom_filename": ROM,
                "rom_sha256_required": USA_SHA256,
                "profile_data_bundled": False,
                "status": "native-modern-root-stock-1p-2p-candidate-only",
            }
            if (set(metadata) != set(expected_headers) | {"immutable_files"}
                    or any(type(metadata.get(k)) is not type(v) or metadata[k] != v
                           for k, v in expected_headers.items())):
                raise ValueError("Baldosa candidate manifest identity, policy or source mismatched")
            listed = metadata.get("immutable_files")
            if (not isinstance(listed, list) or len(listed) != len(PAYLOAD_NAMES)
                    or [x.get("path") if isinstance(x, dict) else None for x in listed]
                       != list(PAYLOAD_NAMES)):
                raise ValueError("Baldosa candidate manifest payload inventory invalid")
            for entry in listed:
                if (set(entry) != {"path", "bytes", "sha256"}
                        or type(entry["bytes"]) is not int or entry["bytes"] <= 0
                        or not isinstance(entry["sha256"], str)
                        or not SHA256.fullmatch(entry["sha256"])):
                    raise ValueError("Baldosa candidate manifest payload metadata invalid")
                member = archive.getinfo(PREFIX + entry["path"])
                if member.file_size != entry["bytes"] or zip_member_digest(archive, member) != entry["sha256"]:
                    raise ValueError("Baldosa candidate payload digest or size mismatch")
            if (archive.read(PREFIX + LAUNCHER) != launcher()
                    or archive.read(PREFIX + README) != readme(source_sha)):
                raise ValueError("Baldosa candidate launcher/README differs from canonical source policy")
    except zipfile.BadZipFile as exc:
        raise ValueError("Baldosa candidate ZIP malformed or corrupt") from exc
    return make_envelope(
        evidence_type="provisional-baldosa-romless-zip-consistency",
        producer="tools/verify_baldosa_romless_candidate_qa.py",
        subject={"backend": "baldosa-aot-provisional",
                 "candidate_commit": source_sha,
                 "candidate_zip_sha256": actual},
        inputs={"artifact_basename": archive_path.name},
        assertions=[
            assertion("independently-nominated-source-and-zip-identity", True),
            assertion("romless-four-member-canonical-zip", True),
            assertion("manifest-and-all-payload-digests", True),
            assertion("canonical-source-launcher-and-readme", True),
        ],
        metrics={"physical_windows_verified": False,
                 "integrated_native_1p_2p_journey_verified": False,
                 "original_gameplay_parity_verified": False},
        outcome="inconclusive",
        provenance={"scope": "read-only ZIP consistency; not executed L4 or L5"},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--expected-zip-sha256", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.zip, args.expected_source, args.expected_zip_sha256)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
