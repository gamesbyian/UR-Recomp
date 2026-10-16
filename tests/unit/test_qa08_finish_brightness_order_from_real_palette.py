"""Native/original 2P finish CGRAM half-math counterfactual, no correction acceptance."""
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_finish_brightness_order_from_real_palette as r


class SourceFiniteColourDiscriminatorTest(unittest.TestCase):
    def test_true_2014_palette_before_and_native_postblend_independent(self):
        main=(13,13,0)
        obj=(15,0,0)
        self.assertEqual(r.original_brightness_then_half(main,obj,7),(49,24,0))
        self.assertEqual(r.native_half_then_output_brightness(main,obj,7),(57,24,0))
        self.assertEqual(r.rgb5(0x01ad),main)
        self.assertEqual(r.rgb5(0x000f),obj)

    def test_full_brightness_trivial_case_equal(self):
        main,obj=(13,13,0),(15,0,0)
        self.assertEqual(r.original_brightness_then_half(main,obj,15),
                         r.native_half_then_output_brightness(main,obj,15))

    def test_invalid_cgram_rejected_before_source_inference(self):
        dummy=json.loads((ROOT/"analysis/data/qa08-two-source-isolated-finish-pixels-20261016.json").read_text())
        with self.assertRaisesRegex(ValueError,"unqualified independently original"):
            r.analyze(b"bad",dummy)
        with self.assertRaisesRegex(ValueError,"unqualified independently original"):
            r.analyze(bytes(512),dummy)
        for invalid in (-1,0x8000):
            with self.assertRaises(ValueError):
                r.rgb5(invalid)
        with self.assertRaises(ValueError):
            r.b5(32,7)


if __name__=="__main__":
    unittest.main()
