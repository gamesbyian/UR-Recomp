#!/usr/bin/env python3
"""ROM-free controls for actual extracted-CMD Modern cold-paint receipts."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from verify_baldosa_windows_extracted_launcher import verify_no_input_modern_paint


OPEN = "UR_BALDOSA_MODERN_ROOT opened=1\n"
ROOT_PAINT = "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared\n"
TITLE_342 = "UR_BALDOSA_MODERN_TITLE painted=1 raster=342x224 host=modern\n"
TITLE_256 = "UR_BALDOSA_MODERN_TITLE painted=1 raster=256x224 host=modern\n"


class ExtractedCmdColdSurfaceTest(unittest.TestCase):
    def test_legacy_immediate_root_and_new_title_are_distinct(self):
        self.assertEqual(verify_no_input_modern_paint(OPEN + ROOT_PAINT), "root")
        for title in (TITLE_342, TITLE_256):
            with self.subTest(title=title):
                self.assertEqual(verify_no_input_modern_paint(OPEN + title), "title")

    def test_reject_missing_duplicate_and_ambiguous_paint(self):
        good = OPEN + TITLE_342
        for bad in (
            "", OPEN, TITLE_342, OPEN + OPEN + TITLE_342,
            good + TITLE_342, OPEN + ROOT_PAINT + TITLE_342,
            OPEN + ROOT_PAINT + ROOT_PAINT,
            OPEN + "UR_BALDOSA_MODERN_TITLE painted=1 raster=999x224 host=modern\n",
            OPEN + "UR_BALDOSA_MODERN_TITLE painted=1 raster=342x224 host=guest\n",
            OPEN + "prefix UR_BALDOSA_MODERN_TITLE painted=1 raster=342x224 host=modern\n",
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                verify_no_input_modern_paint(bad)

    def test_windows_crlf_source_logs_are_accepted(self):
        self.assertEqual(
            verify_no_input_modern_paint((OPEN + TITLE_342).replace("\n", "\r\n")),
            "title",
        )


if __name__ == "__main__":
    unittest.main()
