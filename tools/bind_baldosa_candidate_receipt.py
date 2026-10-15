#!/usr/bin/env python3
"""Bind the exact native executable the Windows journeys ran to the nominated
ROM-free ZIP, and emit one compact hash receipt.

Pure byte/hash arithmetic over the already-built executable and the already-
assembled ZIP: no ROM, saves or new package format. A mismatch fails closed so a
journey can never be credited to a different binary than the one packaged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from assemble_baldosa_windows_candidate import EXE, MANIFEST, PREFIX


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bind(exe: Path, archive: Path, sha_file: Path, revision: str) -> dict:
    for p in (exe, archive, sha_file):
        if p.is_symlink() or not p.is_file():
            raise ValueError("missing or redirected candidate input: " + p.name)
    exe_sha = sha256_file(exe)
    zip_sha = sha256_file(archive)
    line = sha_file.read_text(encoding="ascii").split()
    if len(line) < 2 or not re.fullmatch(r"[0-9a-f]{64}", line[0]) or \
            line[1].lstrip("*") != archive.name:
        raise ValueError("ZIP .sha256 file is not '<sha256>  <archive name>'")
    if line[0] != zip_sha:
        raise ValueError("ZIP bytes do not match its published .sha256")
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read(PREFIX + MANIFEST))
        packaged = hashlib.sha256(z.read(PREFIX + EXE)).hexdigest()
    listed = {i["path"]: i["sha256"] for i in manifest["immutable_files"]}
    if packaged != exe_sha:
        raise ValueError("journey executable differs from packaged executable")
    if listed.get(EXE) != exe_sha:
        raise ValueError("ZIP manifest executable hash differs from journey binary")
    if manifest.get("project_revision") != revision:
        raise ValueError("ZIP manifest revision differs from the tested source revision")
    return {
        "format": "ur-baldosa-windows-candidate-binding-v1",
        "source_revision": revision,
        "zip_name": archive.name,
        "zip_sha256": zip_sha,
        "zip_bytes": archive.stat().st_size,
        "journey_and_packaged_executable_sha256": exe_sha,
        "executable_bytes": exe.stat().st_size,
        "manifest_immutable_files": listed,
        "claims": "hash identity only; not physical-pad, release-gate or "
                  "independent acceptance",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--zip", type=Path, required=True)
    p.add_argument("--zip-sha256-file", type=Path, required=True)
    p.add_argument("--revision", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    receipt = bind(a.exe, a.zip, a.zip_sha256_file, a.revision)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(f"BALDOSA_CANDIDATE_BINDING zip_sha256={receipt['zip_sha256']} "
          f"exe_sha256={receipt['journey_and_packaged_executable_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
