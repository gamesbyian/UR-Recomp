#!/usr/bin/env python3
"""Build fail-closed counterfactual ROMs for unused-song audio reconstruction.

Each case changes only the direct-upload block ID inside an already-reachable
setup/package pair. The surrounding canonical bytes, including the package-table
seed and both long-call targets, are verified before patching.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CANONICAL_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"

CASES = {
    "unused-song-1-demo-package": {
        "ldx_file_offset": 0x001452,
        "from_selector": 0x38,
        "to_selector": 0x3B,
        "package_seed": 0xFB15,
        "track": "Unused Song 1",
        "package": "03:FB15",
    },
    "unused-song-2-race-package": {
        "ldx_file_offset": 0x01CA60,
        "from_selector": 0x3E,
        "to_selector": 0x3D,
        "package_seed": 0xFB55,
        "track": "Unused Song 2",
        "package": "03:FB55",
    },
}

# LDX #selector ; JSL $82:807E ; LDX #package ; JSL $82:82A5
def expected_sequence(selector: int, package_seed: int) -> bytes:
    return bytes([
        0xA2, selector & 0xFF, selector >> 8,
        0x22, 0x7E, 0x80, 0x82,
        0xA2, package_seed & 0xFF, package_seed >> 8,
        0x22, 0xA5, 0x82, 0x82,
    ])


def patch_rom(rom: bytes, case_name: str, *, require_canonical_hash: bool = True) -> tuple[bytes, dict]:
    case = CASES[case_name]
    if require_canonical_hash:
        digest = hashlib.sha256(rom).hexdigest()
        if digest != CANONICAL_SHA256:
            raise ValueError(f"canonical ROM SHA-256 mismatch: {digest}")

    off = case["ldx_file_offset"]
    before = expected_sequence(case["from_selector"], case["package_seed"])
    actual = rom[off:off + len(before)]
    if actual != before:
        raise ValueError(
            f"{case_name}: setup/package bytes differ at 0x{off:06X}: "
            f"expected {before.hex(' ')}, got {actual.hex(' ')}"
        )

    patched = bytearray(rom)
    patched[off + 1] = case["to_selector"]
    after = expected_sequence(case["to_selector"], case["package_seed"])
    if bytes(patched[off:off + len(after)]) != after:
        raise AssertionError("patched byte sequence failed self-check")

    changed = [i for i, (a, b) in enumerate(zip(rom, patched)) if a != b]
    if changed != [off + 1]:
        raise AssertionError(f"expected one changed byte, got {changed}")

    report = {
        "schema_version": 1,
        "case": case_name,
        "track": case["track"],
        "package": case["package"],
        "ldx_file_offset": off,
        "ldx_file_offset_hex": f"0x{off:06X}",
        "patched_file_offset": off + 1,
        "patched_file_offset_hex": f"0x{off + 1:06X}",
        "from_selector": case["from_selector"],
        "from_selector_hex": f"0x{case['from_selector']:02X}",
        "to_selector": case["to_selector"],
        "to_selector_hex": f"0x{case['to_selector']:02X}",
        "package_seed": case["package_seed"],
        "package_seed_hex": f"0x{case['package_seed']:04X}",
        "before_hex": before.hex(" "),
        "after_hex": after.hex(" "),
        "input_sha256": hashlib.sha256(rom).hexdigest(),
        "output_sha256": hashlib.sha256(patched).hexdigest(),
        "changed_byte_count": 1,
    }
    return bytes(patched), report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("case", choices=sorted(CASES))
    ap.add_argument("output", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    patched, report = patch_rom(args.rom.read_bytes(), args.case)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
