#!/usr/bin/env python3
"""Apply exactly one repository-verified host presentation density patch to
Baldosa's disposable pinned framework checkout. No general fork rebase.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PATCH = "tools/patches/snesrecomp-presentation-scale.patch"
HEADER = "runner/src/desktop/host_main.h"
ABI_MARKER = "int (*presentation_scale)(void);"


def apply(root: Path, framework: Path) -> bool:
    root, framework = root.resolve(), framework.resolve()
    info = json.loads((root / "tools/toolchain-entries/snesrecomp.json").read_text())
    pinned = [p for p in info["patches"] if p["path"] == PATCH]
    if len(pinned) != 1:
        raise ValueError("Missing or ambiguous UR-owned presentation scale patch pin")
    source = root / PATCH
    if hashlib.sha256(source.read_bytes()).hexdigest() != pinned[0]["sha256"]:
        raise ValueError("Presentation patch SHA256 does not match toolchain manifest")
    header = framework / HEADER
    if not header.is_file():
        raise ValueError("Pinned Baldosa framework header absent")
    # Never touch the game input/guest/ROM, only the disposable framework
    # host. The host ABI is checked after application.
    if ABI_MARKER in header.read_text():
        return False
    command = ["git", "apply", "--check", str(source)]
    probe = subprocess.run(command, cwd=framework, text=True, capture_output=True)
    if probe.returncode != 0:
        raise ValueError("Single-patch framework ABI conflict: " + probe.stderr.strip()[:900])
    subprocess.run(["git", "apply", str(source)], cwd=framework, check=True)
    if ABI_MARKER not in header.read_text():
        raise ValueError("Patch applied but host density ABI unavailable")
    return True


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--root", type=Path, required=True)
    a.add_argument("--framework", type=Path, required=True)
    args = a.parse_args()
    print("UR_BALDOSA_4X single_presentation_patch_applied=",
          int(apply(args.root, args.framework)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
