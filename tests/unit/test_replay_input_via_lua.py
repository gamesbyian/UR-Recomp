from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from replay_input_via_lua import build_lua, load_runs


class ReplayInputTests(unittest.TestCase):
    def test_load_runs_sorts_and_preserves_masks(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "input.txt"
            p.write_text("10:2:080\n# comment\n0:1:001\n", encoding="utf-8")
            self.assertEqual(load_runs(p), [(0, 1, 0x001), (10, 2, 0x080)])

    def test_load_runs_rejects_overlap(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "input.txt"
            p.write_text("0:4:001\n3:2:080\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                load_runs(p)

    def test_generated_lua_uses_normalized_project_state_addresses(self):
        lua = build_lua([(0, 1, 1)], 2, [0])
        self.assertIn("mainmemory.read_u8(0x0545)", lua)
        self.assertIn("mainmemory.read_u8(0x04C7)", lua)
        self.assertIn("s16(0x04B7)", lua)
        self.assertNotIn("mainmemory.read_u8(0x0F49)", lua)


if __name__ == "__main__":
    unittest.main()
