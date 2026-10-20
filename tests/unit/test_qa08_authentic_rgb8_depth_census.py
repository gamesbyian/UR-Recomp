"""ROM-free RGB5/RGB8 263-source provenance and arithmetic checks."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_authentic_rgb8_depth_census as depth


def sample(first: tuple[int,int,int,int], second: tuple[int,int,int,int]):
    o=bytearray(depth.PIXELS*4)
    n=bytearray(depth.PIXELS*4)
    o[:4]=bytes(first)  # original BGRX
    n[:4]=bytes(second) # native RGBA
    return bytes(o), depth.source.P7_HEADER + bytes(n)


class ActualSourceDepthTests(unittest.TestCase):
    def test_rgb5_exact_can_differ_in_three_low_bits(self):
        # Both sample pixels have R5=20. The source RGB8 bytes differ.
        original,native=sample((0,0,161,0),(166,0,0,0))
        actual=depth.compare(original,native)
        self.assertEqual(actual["wrong_RGB5"],0)
        self.assertEqual(actual["wrong_RGB8"],1)
        self.assertEqual(actual["RGB5_exact_but_RGB8_different"],1)
        self.assertEqual(actual["exact_RGB5"],depth.PIXELS)
        self.assertEqual(actual["exact_RGB8"],depth.PIXELS-1)

    def test_true_rgb5_difference_remains_qualified_error(self):
        original,native=sample((165,166,165,0),(138,138,138,0))
        actual=depth.compare(original,native)
        self.assertEqual(actual["wrong_RGB5"],1)
        self.assertEqual(actual["wrong_RGB8"],1)
        self.assertEqual(actual["RGB5_exact_but_RGB8_different"],0)

    def test_full_uncropped_source_shape_and_alpha_fail_closed(self):
        original,native=sample((0,0,0,0),(0,0,0,0))
        for a,b in ((original[:-1],native),(original,native[:-1]),
                    (original,b"bad"+native[3:])):
            with self.assertRaisesRegex(ValueError,"raster shape"):
                depth.compare(a,b)
        bad=bytearray(original)
        bad[3]=255
        with self.assertRaisesRegex(ValueError,"fourth channel"):
            depth.compare(bytes(bad),native)
        bad=bytearray(native)
        bad[len(depth.source.P7_HEADER)+3]=255
        with self.assertRaisesRegex(ValueError,"fourth channel"):
            depth.compare(original,bytes(bad))

    def test_source_proof_rejected_before_original_or_native_frames_used(self):
        with patch.object(depth.source,"verify",side_effect=ValueError("bad archive")):
            with self.assertRaisesRegex(ValueError,"bad archive"):
                depth.analyze(Path("fake-original.zip"),Path("fake-native.zip"))

    def test_authentic_263_receipt_counts_are_conserved_without_release_promotion(self):
        path=ROOT/"analysis/data/qa08-authentic-rgb8-source-budget-20261019.json"
        data=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["original_2014_Snes9x_inner_sha256"],depth.source.ORIGINAL_INNER_SHA)
        self.assertEqual(data["native_legacy_Win32_outer_sha256"],depth.source.NATIVE_OUTER_SHA)
        self.assertEqual(data["native_nested_P7_sha256"],depth.source.NATIVE_INNER_SHA)
        self.assertEqual(data["total_genuine_source_frames"],263)
        self.assertEqual(data["total_source_pixel_positions"],263*256*224)
        self.assertEqual(data["wrong_RGB5_positions"],890205)
        self.assertEqual(data["wrong_RGB8_positions"],13293424)
        self.assertEqual(data["RGB5_exact_but_RGB8_different"],12403219)
        self.assertEqual(data["RGB5_exact_frames"],132)
        self.assertEqual(data["RGB8_exact_frames"],18)
        self.assertEqual(data["both_precision_exact_pixel_positions"],1788048)
        self.assertEqual(data["wrong_RGB8_positions"],
                         data["wrong_RGB5_positions"]+
                         data["RGB5_exact_but_RGB8_different"])
        for k in ("source_raw_8bit_identical_DAC_proven",
                  "same_2014_SNESC_hardware_color_implementation_proven",
                  "native_effective_CGRAM_causality_proven",
                  "global_recolor_or_brightness_fix_authorized",
                  "QA08_QA10_or_release_accepted"):
            self.assertIs(data[k],False)


if __name__=="__main__":
    unittest.main()
