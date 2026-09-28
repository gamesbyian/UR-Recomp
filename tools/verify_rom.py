#!/usr/bin/env python3
"""Verify a local Uniracers ROM against project-approved hashes."""
from __future__ import annotations
import argparse, hashlib
from pathlib import Path

SUPPORTED = {
    # "sha256": {"label": "Exact verified revision", "size": 0},
}

def digest(path: Path):
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            size += len(chunk)
            h.update(chunk)
    return h.hexdigest(), size

def main():
    p = argparse.ArgumentParser()
    p.add_argument("rom", type=Path)
    args = p.parse_args()
    sha, size = digest(args.rom)
    print(f"file:   {args.rom}")
    print(f"size:   {size} bytes")
    print(f"sha256: {sha}")
    if not SUPPORTED:
        print("\nNo supported ROM digest has been pinned yet.")
        return 2
    hit = SUPPORTED.get(sha)
    if not hit:
        print("\nUNRECOGNIZED ROM")
        return 1
    if hit.get("size") is not None and size != hit["size"]:
        print("\nHASH MATCHED BUT SIZE METADATA DISAGREES")
        return 1
    print(f"\nOK: {hit['label']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
