"""Exact real source 28-frame CGRAM phase, no graphics-release extrapolation."""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_classify_results_cgram_phase as phase

class TestActualOriginalCgramPhase(unittest.TestCase):
    def test_source_phase_uses_fully_verified_sha_and_source_fingerprints(self):
        self.assertEqual(phase.ZIP_SHA,"d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8")
        self.assertEqual(len(phase.SOURCE_WINDOW),16)
        self.assertEqual(phase.SOURCE_WINDOW[0],5073)
        self.assertEqual(phase.SOURCE_WINDOW[-1],5178)
        self.assertEqual(len(phase.SLOTS),4)
        self.assertEqual(len(phase.WORDS),4)
        self.assertEqual(phase.fnv(bytes(512)),"4d7705c5")
        self.assertEqual((28*16)//__import__("math").gcd(28,16),112)

    def test_negative_source_pixel_and_port_checks_not_waived(self):
        with self.assertRaises(ValueError):
            phase.fnv(bytes(511))
        with self.assertRaises(ValueError):
            phase.decode(b"forged port chronology")
        with self.assertRaises(ValueError):
            phase.analyze(b"bad",bytes(512),{})
        source=(ROOT/"tools/qa08_classify_results_cgram_phase.py").read_text()
        self.assertIn("263_original_unmasked_BGRX_frames_identical_to_prior_original",source)
        self.assertIn("fingerprint_not_raw_native_CGRAM_byte_equality",source)
        self.assertIn("graphics_release_ledger_gates_accepted",source)
        self.assertNotIn("forcepoke(",source)

if __name__=="__main__":
    unittest.main()
