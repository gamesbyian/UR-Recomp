"""ROM-free admission tests for exact Modern root geometry event tokens.

An authenticated log hash protects bytes, not semantic identity of the event.
Reject prefixed markers and conflicting duplicated fields even if a
receipt was recomputed over the tampered process log.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_modern_root_sdl_contrast as audit


class NativeRootGeometryTokenTests(unittest.TestCase):
    def test_exact_root_geometry_admitted(self):
        line = ("UR_BALDOSA_MODERN_DESTINATION stage=root raster=342x224 "
                "root=11,10,320,204 source=modern_product_view")
        self.assertEqual(audit.native_root_geometry(line),
                         (342, 224, 11, 10, 320, 204))

    def test_reject_spoofed_root_events(self):
        real = ("UR_BALDOSA_MODERN_DESTINATION stage=root raster=342x224 "
                "root=11,10,320,204 source=modern_product_view")
        for line in (
            "FAKE_" + real,
            "debug: " + real,
            real.replace("stage=root", "stage=rootish"),
            real.replace("raster=342x224", "raster=342x224FAKE"),
            real.replace("root=11,10,320,204", "root=11,10,320,204FAKE"),
            real + " raster=256x224",
            real + " root=8,10,240,204",
            real + " stage=title",
            real + " comment-without-equals",
        ):
            with self.subTest(line=line):
                self.assertIsNone(audit.native_root_geometry(line))

    def test_field_order_and_unrelated_events(self):
        self.assertEqual(audit.native_root_geometry(
            "UR_BALDOSA_MODERN_DESTINATION root=8,10,240,204 "
            "source=modern_product_view raster=256x224 stage=root"),
            (256, 224, 8, 10, 240, 204))
        self.assertIsNone(audit.native_root_geometry(
            "UR_BALDOSA_MODERN_DESTINATION stage=title raster=342x224 "
            "root=11,10,320,204"))

    def test_garbage_or_incomplete_event_is_not_source_evidence(self):
        for event in ("", "UR_BALDOSA_MODERN_DESTINATION", 
                      "UR_BALDOSA_MODERN_DESTINATION stage=root raster=342x224",
                      "UR_BALDOSA_MODERN_DESTINATION stage=root raster=342x224 root=",
                      "UR_BALDOSA_MODERN_DESTINATION stage=root raster=+342x224 root=11,10,320,204"):
            with self.subTest(event=event):
                self.assertIsNone(audit.native_root_geometry(event))


if __name__ == "__main__":
    unittest.main()
