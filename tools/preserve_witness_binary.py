#!/usr/bin/env python3
"""Verify and describe an exact witness native candidate before retention.

Used by ``research-preserve-witness-binary.yml``. Refuses a tarball whose
native executable does not match the witness's recorded SHA-256, or that
contains ROM image files. Writes a compact manifest; grants no credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

SCHEMA = "ur-research-witness-binary/1"
EXECUTABLE = "shared-modern-native/UniracersSNESRecomp/build/UniracersSNESRecomp"
ROM_SUFFIXES = (".sfc", ".smc", ".swc", ".fig")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect(tarball: Path, expected: str) -> dict:
    if not tarball.is_file() or tarball.is_symlink():
        raise ValueError("missing candidate tarball")
    with tarfile.open(tarball, "r:gz") as archive:
        members = archive.getmembers()
        roms = [m.name for m in members if m.name.lower().endswith(ROM_SUFFIXES)]
        if roms:
            raise ValueError(f"candidate tarball contains ROM image files: {roms[:3]}")
        exe = next((m for m in members if m.name == EXECUTABLE and m.isfile()), None)
        if exe is None:
            raise ValueError("candidate tarball lacks the native executable")
        handle = archive.extractfile(exe)
        actual = sha256_bytes(handle.read() if handle else b"")
    if actual != expected:
        raise ValueError(f"executable SHA-256 {actual} does not match witness {expected}")
    return {"executable_path": EXECUTABLE, "executable_sha256": actual,
            "tarball_sha256": sha256_bytes(tarball.read_bytes()),
            "tarball_bytes": tarball.stat().st_size, "members": len(members),
            "rom_image_files": 0}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tarball", type=Path, required=True)
    ap.add_argument("--expected-executable-sha256", required=True)
    ap.add_argument("--source-run-id", type=int, required=True)
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--summary", type=Path)
    args = ap.parse_args()
    manifest = {"schema": SCHEMA, "source_run_id": args.source_run_id,
                "source_artifact": args.artifact,
                **inspect(args.tarball, args.expected_executable_sha256),
                "release_gate_credit": 0, "original_native_parity": False}
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if args.summary:
        with args.summary.open("a", encoding="utf8") as out:
            out.write(f"### Witness binary preserved\n\nRun {args.source_run_id} `{args.artifact}`: "
                      f"executable `{manifest['executable_sha256']}` verified; no ROM files. "
                      "Retained 90 days as `research-witness-native-"
                      f"{args.source_run_id}`. No gameplay or release credit.\n")
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
