import tempfile
import unittest
from pathlib import Path

from tools.assert_uniracers_vs_oam_seam import assert_vs_oam_seam, parse_ppuw


class VsOamSeamTests(unittest.TestCase):
    def test_parse_and_assert_canonical_vs_seam(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "race.ppuw.tsv"
            path.write_text(
                "1140\t0\t283\t2104\tA5\thdma\n"
                "1140\t112\t284\t2104\t5A\thdma\n"
                "1140\t229\t10\t2104\t44\tdma\n",
                encoding="utf-8",
            )
            rows = parse_ppuw(path)
            self.assertEqual(len(rows), 3)
            result = assert_vs_oam_seam([path])[0]
            self.assertEqual(result["v0_values"], [0xA5])
            self.assertEqual(result["v112_values"], [0x5A])

    def test_missing_scanline_112_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.ppuw.tsv"
            path.write_text("1\t0\t10\t2104\tA5\thdma\n", encoding="utf-8")
            with self.assertRaises(AssertionError):
                assert_vs_oam_seam([path])


if __name__ == "__main__":
    unittest.main()
