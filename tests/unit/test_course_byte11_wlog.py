#!/usr/bin/env python3
"""Regression test for exact course-byte write-log summarization."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "summarize_course_byte11_wlog.py"


class CourseByte11WlogTests(unittest.TestCase):
    def test_filters_bank_and_preserves_exact_ipc(self):
        lines = [
            "f867    7E:000B=AA w1 interp@$81FFFF A=0000 IPC=81AAAA",
            "f867    7F:000B=0F w1 interp@$81BB73 A=1234 X=0000 IPC=81BC10",
            "f879    7F:000B=10 w1 interp@$81BA96 A=0000 X=0000 IPC=81BC42",
            "f879    7F:000B=11 w1 interp@$81BA96 A=0000 X=0000 IPC=81BC42",
        ]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "wlog.txt"
            out = td / "out.json"
            src.write_text("\n".join(lines) + "\n", encoding="utf-8")
            subprocess.run(
                [sys.executable, str(TOOL), str(src), "--json-out", str(out)],
                check=True,
            )
            d = json.loads(out.read_text())
            self.assertEqual(d["values"], [0x0F, 0x10, 0x11])
            self.assertEqual(
                d["unique_ipcs"],
                [0x81BC10, 0x81BC42],
            )
            self.assertEqual(
                d["unique_scopes"],
                ["interp@$81BA96", "interp@$81BB73"],
            )
            self.assertTrue(all(w["width"] == 1 for w in d["writes"]))


if __name__ == "__main__":
    unittest.main()
