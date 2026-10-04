import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import compare_engine_screen_text as cmp  # noqa: E402
import extract_menu_visual_language as mvl  # noqa: E402


class EngineTextParityTests(unittest.TestCase):
    def test_missing_line_is_reported(self) -> None:
        ref = {"race-results": ["DRAGSTER", "MIKE", "0:28.56", "SOMEONE"]}
        nat = {"race-results": ["DRAGSTER", "MIKE", "SOMEONE"]}
        r = cmp.compare(ref, nat)["race-results"]
        self.assertFalse(r["match"])
        self.assertEqual(r["missing_on_native"], ["0:28.56"])
        self.assertTrue(cmp.compare(ref, ref)["race-results"]["match"])

    def test_native_regs_adapter(self) -> None:
        regs = {"bgsc": [2, 19, 0, 0], "bg_tile_adr": 0x23, "hscroll": [0, 256, 0, 0], "vscroll": [79, 8, 0, 0]}
        out = mvl.native_regs_as_snesref(regs)
        self.assertEqual(out["fillram"]["2108"], "13")
        self.assertEqual(out["fillram"]["210B"], "23")
        self.assertEqual(out["ppu"]["bg"][1], {"hofs": 256, "vofs": 8})


if __name__ == "__main__":
    unittest.main()
