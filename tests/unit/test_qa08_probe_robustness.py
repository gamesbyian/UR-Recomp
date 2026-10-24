"""ROM-free future chromatic-probe model diagnostics, not raster parity."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from qa08_probe_robustness import expand,predict,choose_probe,genuine_scale_compatibility

class ChromaticProbeModelTest(unittest.TestCase):
    def test_stable_model_has_twelve_distinct_exact_predictions(self):
        p=predict((5,13,22))
        self.assertEqual(len(p),12)
        self.assertEqual(len(set(p.values())),12)

    def test_grayscale_model_is_not_chromatic_evidence(self):
        self.assertLess(len(set(predict((5,5,5)).values())),12)

    def test_selects_future_probe_without_claiming_observation(self):
        p=choose_probe()
        self.assertEqual(p['distinct_exact_predictions'],12)
        self.assertGreaterEqual(p['minimum_pairwise_L1'],3)
        self.assertTrue(p['plus_minus_one_measurement_cannot_uniquely_identify_scaling'])
        self.assertFalse(p['same_epoch_ppu_proven'])
        self.assertEqual(p['release_gate_credit'],0)

    def test_rejects_invalid_rgb5_inputs(self):
        for invalid in (-1,32,True,3.5):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                expand(invalid)
        for invalid in ((0,0,32),(3,3),[3,4,5]):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                predict(invalid)

    def test_unpinned_archive_never_enters_genuine_evidence(self):
        with self.assertRaisesRegex(ValueError,'unauthenticated'):
            genuine_scale_compatibility(Path(__file__))

if __name__=='__main__':unittest.main()
