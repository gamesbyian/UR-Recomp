#!/usr/bin/env python3
"""Regression tests for imported reference integrity audit."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "audit_imported_references.py"

spec = importlib.util.spec_from_file_location("audit_imported_references", TOOL)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def main() -> int:
    assert mod.git_blob_sha1(b"test") == hashlib.sha1(b"blob 4\0test").hexdigest()
    failures = mod.verify()
    assert failures == [], failures

    subprocess.run([sys.executable, str(TOOL)], check=True)

    manifest = mod.load_manifest()
    by_path = {x["path"]: x for x in manifest["entries"]}

    cheat = by_path["reference/imported/libretro/Uniracers (USA).cht"]
    assert cheat["git_blob_sha1"] == "c7cc8c948b105aef6db8af18188b56b6fcd43bf8"
    assert cheat["upstream_git_blob_sha1"] == cheat["git_blob_sha1"]

    bot = by_path["reference/imported/tas-bots/uniracers-tabletop-bot-2014.lua"]
    assert bot["category"] == "bot-source"
    assert bot["review_status"] == "audited-known-defects"
    assert bot["external_sha256"] == (
        "9183b89f27e153b5db450134c00fb98f47d67c47e979a189ae51bcd8c06629c6"
    )

    dos = by_path["reference/imported/tools/rnc_propack-2.14/PPIBM.EXE"]
    assert dos["category"] == "historical-executable"
    assert dos["review_status"] == "archive-only-never-execute"
    assert dos["upstream_git_blob_sha1"] == dos["git_blob_sha1"]

    print("PASS: imported corpus is exhaustive, byte-pinned and non-executable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
