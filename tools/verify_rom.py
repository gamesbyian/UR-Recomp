#!/usr/bin/env python3
"""Verify the canonical Uniracers ROM used by UR-Recomp."""
from __future__ import annotations
import argparse, hashlib, zlib
from pathlib import Path

EXPECTED = {
    "size": 2097152,
    "crc32": "383858c7",
    "sha256": "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("rom", nargs="?", default="reference/roms/retail/Uniracers_USA.sfc", type=Path)
    args=p.parse_args()
    data=args.rom.read_bytes()
    got={
        "size": len(data),
        "crc32": f"{zlib.crc32(data)&0xffffffff:08x}",
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    for k,v in got.items():
        print(f"{k}: {v}")
    bad=[k for k in EXPECTED if got[k] != EXPECTED[k]]
    if bad:
        print("ROM MISMATCH:", ", ".join(bad))
        return 1
    print("OK: canonical UR-Recomp Uniracers (USA) ROM")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
