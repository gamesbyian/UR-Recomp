#!/usr/bin/env python3
"""Import only the already-owned split-band world-shadow patch to Baldosa.

The pinned Ema framework has world-keyed shadow margins but lacks the
WsShadowSetSplit / WsShadowSetLine API required by UR's tested 2P margin
provider. Validate SHA256 provenance and three exact ABI anchors; modify only
a disposable checkout, never the project toolchain's pinned framework.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PATCH = "tools/patches/snesrecomp-ws-shadow-split-band.patch"
HEADER = "runner/src/snes/ws_shadow.h"
SHADOW = "runner/src/snes/ws_shadow.c"
PPU = "runner/src/snes/ppu.c"
REQUIRED = {
    HEADER: ("void WsShadowSetSplit(", "void WsShadowSetLine("),
    SHADOW: ("void WsShadowSetSplit(", "void WsShadowSetLine(int line)"),
    PPU: ("WsShadowSetLine(y);",),
}


def apply(root: Path, framework: Path) -> bool:
    root, framework = root.resolve(), framework.resolve()
    manifest = json.loads((root / "tools/toolchain-entries/snesrecomp.json").read_text())
    entry = [e for e in manifest["patches"] if e["path"] == PATCH]
    if len(entry) != 1:
        raise ValueError("Missing or duplicated project split-band patch manifest pin")
    source = root / PATCH
    if hashlib.sha256(source.read_bytes()).hexdigest() != entry[0]["sha256"]:
        raise ValueError("Pinned split-band patch digest mismatch")
    for name in REQUIRED:
        if not (framework / name).is_file():
            raise ValueError("Pinned framework missing required world-shadow source: " + name)
    if all(all(token in (framework / name).read_text() for token in tokens)
           for name, tokens in REQUIRED.items()):
        return False
    check = subprocess.run(
        ["git", "apply", "--check", str(source)], cwd=framework,
        capture_output=True, text=True)
    if check.returncode:
        raise ValueError("Baldosa split-band ABI patch conflict: " +
                         check.stderr.strip()[:1000])
    subprocess.run(["git", "apply", str(source)], cwd=framework, check=True)
    for name, tokens in REQUIRED.items():
        body = (framework / name).read_text()
        if any(token not in body for token in tokens):
            raise ValueError("Split-band patch applied with incomplete ABI: " + name)
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--framework", type=Path, required=True)
    a = p.parse_args()
    print("UR_BALDOSA_WS24 split_band_patch_applied=",
          int(apply(a.root, a.framework)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
