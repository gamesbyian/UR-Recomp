#!/usr/bin/env python3
"""ROM-free regression for tools/summarize_usjo8_checkpoints.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "summarize_usjo8_checkpoints.py"


def put16(blob: bytearray, addr: int, value: int) -> None:
    value &= 0xFFFF
    blob[addr] = value & 0xFF
    blob[addr + 1] = value >> 8


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        blob = bytearray(0x20000)
        put16(blob, 0x04B7, -123)
        put16(blob, 0x04BB, 456)
        values = {
            0x0545: 1, 0x0F61: 2, 0x042F: 3, 0x042B: 4,
            0x11F9: 5, 0x11FD: 6, 0x0DFD: 7, 0x0F57: 8, 0x11CD: 9, 0x11CE: 10,
        }
        for addr, value in values.items():
            blob[addr] = value
        put16(blob, 0x11CF, 0x1234)
        put16(blob, 0x11D1, 0x5678)
        (td / "probe.wram.bin").write_bytes(blob)
        out = td / "out.json"
        subprocess.run([
            sys.executable, str(TOOL), str(td),
            "--checkpoint", "probe", "--json-out", str(out)
        ], check=True)
        row = json.loads(out.read_text())["probe"]
        assert row == {
            "x_speed": -123,
            "y_speed": 456,
            "air": 1,
            "twists": 2,
            "tabletops": 3,
            "zflips": 4,
            "rolls": 5,
            "flips": 6,
            "z_rotation": 7,
            "z_pre_rotation": 8,
            "boost_meter_low": 9,
            "boost_meter_high": 10,
            "boost_meter_word": 2569,
            "p1_boost_persistent": 0x1234,
            "p2_boost_persistent": 0x5678,
        }, row

    # Do not admit a partial or extended WRAM file as authoritative evidence.
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for name, length in (("truncated", 0x1FFFF), ("extended", 0x20001)):
            (td / f"{name}.wram.bin").write_bytes(bytes(length))
            probe = subprocess.run([
                sys.executable, str(TOOL), str(td), "--checkpoint", name
            ], text=True, capture_output=True)
            assert probe.returncode != 0, (name, probe.stdout)
            assert "expected 131072 bytes" in probe.stderr, (name, probe.stderr)

    print("PASS: USJO v8 checkpoint summarizer field widths and signs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
