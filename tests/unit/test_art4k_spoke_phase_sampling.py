"""No-ROM rational negative controls for aliasing of 2026 source spokes."""
import unittest
from fractions import Fraction
from tools.art.audit_art4k_spoke_phase_sampling import analyze,parse_time,phase_modulo_spokes


class SourceSpokeSamplingTests(unittest.TestCase):
    def test_historical_eighth_phase_grid_cannot_distinguish_spoke_orientation(self):
        r=analyze([str(Fraction(i,8)) for i in range(9)])
        self.assertTrue(r["all_samples_spoke_aliased"])
        self.assertEqual(r["unique_spoke_set_orientations"],1)
        self.assertEqual(set(r["relative_spoke_phase_modulo_45_degrees"]),{"0"})
        self.assertFalse(r["source_ride_animation_1994_ppu_cadence_verified"])

    def test_older_quarter_grid_is_also_spoke_aliased(self):
        r=analyze([str(Fraction(i,4)) for i in range(5)])
        self.assertTrue(r["all_samples_spoke_aliased"])

    def test_fine_grid_reveals_four_spoke_orientations(self):
        r=analyze(["0","1/64","1/32","3/64","1/16"])
        self.assertFalse(r["all_samples_spoke_aliased"])
        self.assertEqual(r["unique_spoke_set_orientations"],4)
        self.assertEqual(r["relative_spoke_phase_modulo_45_degrees"],
                         ["0","45/4","45/2","135/4","0"])

    def test_exact_spoke_period_and_reorder_alias(self):
        for i in range(9):
            self.assertEqual(phase_modulo_spokes(Fraction(i,16)),Fraction(0))
        self.assertEqual(phase_modulo_spokes(Fraction(1,64)),Fraction(45,4))

    def test_duplicate_or_backward_sample_rejected(self):
        for values in ([],["0","0"],["0","0/2"],["1/32","0"]):
            with self.subTest(values=values),self.assertRaises(ValueError):
                analyze(values)

    def test_invalid_time_does_not_become_animation_observation(self):
        for value in ("-1/64","65/64","NaN","Infinity","1/0","1/65537",
                      "","2",None,True,0.5):
            with self.subTest(value=value),self.assertRaises(ValueError):
                parse_time(value)


if __name__=="__main__":
    unittest.main()
