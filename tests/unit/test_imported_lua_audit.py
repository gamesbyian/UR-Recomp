from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from audit_imported_lua import find_duplicate_table_keys


class LuaAuditTests(unittest.TestCase):
    def test_detects_duplicate_named_key_in_same_table(self):
        src = """
        x = {
          a = 1,
          child = { a = 9 },
          a = 2,
        }
        """
        findings = find_duplicate_table_keys(src)
        self.assertEqual([(f.key, f.first_line, f.duplicate_line) for f in findings], [("a", 3, 5)])

    def test_recovered_bot_known_duplicate_keys_remain_visible(self):
        path = ROOT / "references/imported/tas-bots/uniracers-tabletop-bot-2014.lua"
        findings = find_duplicate_table_keys(path.read_text(encoding="utf-8"))
        keys = {f.key for f in findings}
        self.assertTrue(
            {"airValue", "showingArrows", "arrowDirection", "currentTrack",
             "inRace", "reverseControls", "pitch", "tabletops"}.issubset(keys)
        )


if __name__ == "__main__":
    unittest.main()
