from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "compare_input_runs.py"


class CompareInputRunsTests(unittest.TestCase):
    def test_comments_do_not_affect_equivalence(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            a = td / "a.input"
            b = td / "b.input"
            a.write_text("# generated\n0:1:001\n10:2:080\n", encoding="utf-8")
            b.write_text("# frozen with different prose\n10:2:080\n0:1:001\n", encoding="utf-8")
            subprocess.run([sys.executable, str(TOOL), str(a), str(b)], check=True)

    def test_real_interval_difference_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            a = td / "a.input"
            b = td / "b.input"
            a.write_text("0:1:001\n", encoding="utf-8")
            b.write_text("0:1:002\n", encoding="utf-8")
            p = subprocess.run([sys.executable, str(TOOL), str(a), str(b)])
            self.assertNotEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
