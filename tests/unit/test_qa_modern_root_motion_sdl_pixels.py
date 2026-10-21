"""ROM-free refusal tests for real SDL root-motion four-frame audit."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools import qa_modern_root_motion_sdl_pixels as qa


class MotionP7VerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.header=(b"P7\nWIDTH 1280\nHEIGHT 720\nDEPTH 4\n"
                     b"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
        self.w,self.h=1280,720
        self.original=bytearray(b"\x20\x33\x45\x00"*(self.w*self.h))
        self.keys=("normal_tick0","normal_tick10",
                   "reduced_tick0","reduced_tick10")

    def pack(self, *,no_motion=False,bad_region=False,
             reduced_changes=False,large_change=False):
        for key in self.keys:
            raw=bytearray(self.original)
            if key=="normal_tick10" and not no_motion:
                if large_change:
                    for y in range(210,280):
                        for x in range(40,100):
                            raw[(y*self.w+x)*4]=255
                else:
                    x,y=(220,220) if bad_region else (61,226)
                    for dy in range(2):
                        for dx in range(2):
                            raw[((y+dy)*self.w+x+dx)*4]=255
            if key=="reduced_tick10" and reduced_changes:
                raw[(221*self.w+62)*4]=255
            (self.root/f"{key}.pam").write_bytes(self.header+raw)

    def check(self):
        return qa.compare(*(self.root/f"{key}.pam" for key in self.keys))

    def test_real_native_reduced_is_stable_and_normal_marker_changes(self):
        self.pack()
        result=self.check()
        self.assertEqual(result["normal_changed_pixel_count"],4)
        self.assertEqual(result["normal_change_bounds"],[61,226,62,227])
        self.assertTrue(result["reduced_motion_all_p7_pixels_identical"])
        self.assertFalse(result["hardware_approved"])
        self.assertEqual(result["release_gate_credit"],0)

    def test_absent_normal_motion_is_not_accepted_as_valid_animation(self):
        self.pack(no_motion=True)
        with self.assertRaisesRegex(qa.MotionPixelAuditError,"does not move"):
            self.check()

    def test_reduced_motion_pixel_flicker_is_rejected(self):
        self.pack(reduced_changes=True)
        with self.assertRaisesRegex(qa.MotionPixelAuditError,"changes with injected tick"):
            self.check()

    def test_nonselection_pixel_motion_is_not_laundered_into_small_effect(self):
        self.pack(bad_region=True)
        with self.assertRaisesRegex(qa.MotionPixelAuditError,"outside narrow cursor"):
            self.check()

    def test_large_unbounded_motion_change_rejected(self):
        self.pack(large_change=True)
        with self.assertRaisesRegex(qa.MotionPixelAuditError,"too much"):
            self.check()

    def test_original_native_p7_required_at_exact_output_dimensions(self):
        self.pack()
        (self.root/"normal_tick10.pam").write_bytes(b"P6\n1280 720\n255\n")
        with self.assertRaisesRegex(qa.MotionPixelAuditError,"wrong P7 header"):
            self.check()


if __name__=="__main__":
    unittest.main()
