#!/usr/bin/env python3
"""Publish only the exact smoke-built PE and a source/ZIP binding, never ROM bytes.

The original full portable ZIP stays on the Windows runner. This is a
non-runnable, ROM-free audit artifact, not a replacement release package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import struct

EXE = "UniracersSNESRecomp.exe"
SHA = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
MAX_EXE_BYTES = 128 * 1024 * 1024
MAX_MANIFEST_BYTES = 8 * 1024 * 1024


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def regular(path: Path, limit: int | None = None) -> None:
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode) or (limit is not None and path.stat().st_size > limit):
        raise ValueError("unsafe or oversized input: " + path.name)


def check_amd64_pe(exe: Path) -> None:
    with exe.open("rb") as stream:
        head = stream.read(64)
        if len(head) != 64 or head[:2] != b"MZ":
            raise ValueError("not an MZ executable")
        offset = struct.unpack_from("<I", head, 0x3c)[0]
        if offset < 64 or offset > 1024 * 1024:
            raise ValueError("invalid PE offset")
        stream.seek(offset)
        signature = stream.read(26)
        if (len(signature) != 26 or signature[:4] != b"PE\0\0"
                or struct.unpack_from("<H", signature, 4)[0] != 0x8664
                or struct.unpack_from("<H", signature, 24)[0] != 0x20b):
            raise ValueError("not an AMD64 PE32+ executable")


def stage(package: Path, archive: Path, checksum: Path,
          source: str, output: Path) -> dict:
    if not SHA.fullmatch(source):
        raise ValueError("source commit must be exact lowercase 40-hex")
    if output.exists() or output.is_symlink():
        raise ValueError("evidence destination already exists")
    for parent in output.parents:
        if parent.is_symlink() or getattr(parent, "is_junction", lambda: False)():
            raise ValueError("evidence destination has redirected ancestor")
    # The evidence output must never modify the verified shipping package.
    if output.resolve().is_relative_to(package.resolve()):
        raise ValueError("evidence output overlaps original package")
    exe = package / EXE
    manifest_file = package / "PACKAGE-MANIFEST.json"
    for path, limit in ((exe, MAX_EXE_BYTES),
                        (manifest_file, MAX_MANIFEST_BYTES),
                        (archive, None), (checksum, 256)):
        regular(path, limit)
    check_amd64_pe(exe)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("source_revision") != source or not isinstance(manifest.get("files"), list):
        raise ValueError("package manifest source mismatch")
    matches = [row for row in manifest["files"]
               if isinstance(row, dict) and row.get("path") == EXE]
    exe_hash = digest(exe)
    if (len(matches) != 1 or matches[0].get("size") != exe.stat().st_size
            or matches[0].get("sha256") != exe_hash):
        raise ValueError("packaged PE differs from manifest")
    zip_hash = digest(archive)
    sidecar = checksum.read_text(encoding="ascii")
    if not DIGEST.fullmatch(zip_hash) or sidecar != f"{zip_hash}  {archive.name}\n":
        raise ValueError("portable ZIP checksum mismatch")
    receipt = {
        "schema": "ur-windows-smoke-romfree-pe-binding/1",
        "source_commit": source,
        "original_portable_zip_sha256": zip_hash,
        "original_manifest_sha256": digest(manifest_file),
        "executable_sha256": exe_hash,
        "executable_bytes": exe.stat().st_size,
        "original_zip_uploaded": False,
        "rom_or_player_data_uploaded": False,
        "release_gate_credit": 0,
        "physical_windows_accepted": False,
    }
    output.mkdir(parents=True)
    staged_exe = output / EXE
    shutil.copyfile(exe, staged_exe)
    if digest(staged_exe) != exe_hash:
        staged_exe.unlink()
        raise ValueError("staged PE differs from original")
    (output / "binding.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--checksum", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = stage(args.package, args.archive, args.checksum,
                   args.source, args.output)
    print("WINDOWS_SMOKE_ROMFREE_PE_BOUND " + result["executable_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
