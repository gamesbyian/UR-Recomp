#!/usr/bin/env python3
"""Create a controlled mutated ROM copy plus a machine-readable mutation record.

Never edits the input in place. Patch syntax is OFFSET=HEXBYTES, where OFFSET may
be decimal or 0x-prefixed and HEXBYTES is an even-length hexadecimal string.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_patch(spec: str) -> tuple[int, bytes]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("patch must be OFFSET=HEXBYTES")
    off_s, hex_s = spec.split("=", 1)
    try:
        offset = int(off_s, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid offset: {off_s}") from exc
    try:
        payload = bytes.fromhex(hex_s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid hex bytes: {hex_s}") from exc
    if not payload:
        raise argparse.ArgumentTypeError("patch payload must not be empty")
    return offset, payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--patch", action="append", type=parse_patch, required=True)
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args()

    src = args.input.resolve()
    dst = args.output.resolve()
    if src == dst:
        raise SystemExit("refusing to mutate ROM in place")

    original = src.read_bytes()
    mutated = bytearray(original)
    changes = []
    occupied: set[int] = set()
    for offset, payload in args.patch:
        end = offset + len(payload)
        if offset < 0 or end > len(mutated):
            raise SystemExit(f"patch 0x{offset:X}..0x{end:X} is outside {len(mutated)}-byte input")
        overlap = [i for i in range(offset, end) if i in occupied]
        if overlap:
            raise SystemExit(f"overlapping patch at 0x{overlap[0]:X}")
        old = bytes(mutated[offset:end])
        mutated[offset:end] = payload
        occupied.update(range(offset, end))
        changes.append({
            "offset": offset,
            "offset_hex": f"0x{offset:06X}",
            "before": old.hex(),
            "after": payload.hex(),
        })

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(mutated)
    record = {
        "schema_version": 1,
        "input": str(args.input),
        "output": str(args.output),
        "input_size": len(original),
        "input_sha256": sha256(original),
        "output_sha256": sha256(mutated),
        "changes": changes,
    }
    manifest = args.manifest or dst.with_suffix(dst.suffix + ".mutation.json")
    manifest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
