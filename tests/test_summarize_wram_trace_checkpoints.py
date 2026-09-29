#!/usr/bin/env python3
"""ROM-free regression test for tools/summarize_wram_trace_checkpoints.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "summarize_wram_trace_checkpoints.py"


def rec(f, adr, old, val):
    return {"f": f, "adr": f"0x{adr:05x}", "old": f"0x{old:02x}", "val": f"0x{val:02x}"}


def main() -> int:
    rows = [
        # Initial state at frame 0.
        rec(0, 0x009F, 0, 0x16),
        rec(0, 0x0313, 0, 0x00),
        rec(0, 0x00CE, 0, 0x03),
        rec(0, 0x0411, 0, 0x40),
        rec(0, 0x0412, 0, 0x04),   # x=1088
        rec(0, 0x0415, 0, 0x5A),
        rec(0, 0x0416, 0, 0x03),   # y=858
        rec(0, 0x04B7, 0, 0x00),
        rec(0, 0x04B8, 0, 0x00),
        rec(0, 0x04BB, 0, 0x00),
        rec(0, 0x04BC, 0, 0x00),
        rec(0, 0x0545, 0, 0x00),
        rec(0, 0x04C7, 0, 0x07),
        rec(0, 0x04C8, 0, 0x00),
        # A pre-race transient 0x99 must not be mistaken for race completion.
        rec(5, 0x009F, 0x16, 0x99),
        rec(6, 0x009F, 0x99, 0x16),
        # Race begins at frame 10.
        rec(10, 0x0313, 0x00, 0x01),
        # By frame 12, x=1100 and signed vx=-2.
        rec(12, 0x0411, 0x40, 0x4C),
        rec(12, 0x04B7, 0x00, 0xFE),
        rec(12, 0x04B8, 0x00, 0xFF),
        # Results at frame 20.
        rec(20, 0x009F, 0x16, 0x99),
        rec(20, 0x0313, 0x01, 0x00),
    ]

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        trace = td / "trace.jsonl"
        trace.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
        jout = td / "out.json"
        tout = td / "out.tsv"
        subprocess.run(
            [
                sys.executable, str(TOOL), str(trace),
                "--checkpoint", "0",
                "--checkpoint", "10",
                "--checkpoint", "11",
                "--checkpoint", "12",
                "--checkpoint", "19",
                "--checkpoint", "20",
                "--json-out", str(jout),
                "--tsv-out", str(tout),
            ],
            check=True,
        )
        report = json.loads(jout.read_text())
        by_frame = {x["frame"]: x for x in report["checkpoints"]}
        assert report["first_in_race_frame"] == 10
        assert report["first_race_results_frame"] == 20
        assert by_frame[0]["x"] == 1088
        assert by_frame[11]["x"] == 1088
        assert by_frame[12]["x"] == 1100
        assert by_frame[12]["vx"] == -2
        assert by_frame[19]["inRace"] == 1
        assert by_frame[20]["menu"] == 0x99
        assert by_frame[20]["inRace"] == 0

    print("PASS: WRAM trace checkpoint reconstruction and transitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
