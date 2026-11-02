"""Source-locked negative controls for canonical versus hypothetical spokes."""
import pathlib
import unittest
from fractions import Fraction
from tools.art.audit_art4k_spoke_phase_sampling import (
    analyze,parse_time,phase_modulo_spokes,verify_canonical_source,
)

FIXTURE=pathlib.Path(__file__).resolve().parents[1]/"fixtures"/"art4k"/"unicycle_shared_rig_2026.scad"


class SourceSpokeSamplingTests(unittest.TestCase):
    def test_canonical_source_has_stationary_rim_independent_of_pedals(self):
        source=FIXTURE.read_bytes()
        verify_canonical_source(source)
        r=analyze(["0","1/64","1/32","3/64","1/16"],canonical_source=source)
        self.assertTrue(r["canonical_source_digest_and_contract_checked"])
        self.assertEqual(r["canonical_rim_unique_spoke_set_orientations"],1)
        self.assertEqual(r["canonical_rim_spoke_phase_modulo_45_degrees"],["11"]*5)
        self.assertFalse(r["canonical_rim_rotates_with_pedals"])
        self.assertFalse(r["counterfactual_direct_drive_implemented_in_canonical_rig"])

    def test_source_drift_and_fake_rotating_rim_rejected(self):
        source=FIXTURE.read_bytes()
        for changed in (source.replace(b"a=i*45+11;",b"a=i*45+12;"),
                        source.replace(b"rim_and_hub();",b"rim_and_hub(pedal);")):
            with self.assertRaisesRegex(ValueError,"digest mismatch"):
                verify_canonical_source(changed)

    def test_historical_eighth_grid_aliased_only_under_counterfactual(self):
        r=analyze([str(Fraction(i,8)) for i in range(9)])
        self.assertTrue(r["counterfactual_direct_drive_samples_aliased"])
        self.assertEqual(r["counterfactual_direct_drive_unique_spoke_set_orientations"],1)
        self.assertEqual(set(r["counterfactual_direct_drive_spoke_phase_modulo_45_degrees"]),{"0"})
        self.assertFalse(r["canonical_source_digest_and_contract_checked"])
        self.assertFalse(r["source_ride_animation_1994_ppu_cadence_verified"])

    def test_older_quarter_grid_is_also_counterfactually_aliased(self):
        self.assertTrue(analyze([str(Fraction(i,4)) for i in range(5)])[
            "counterfactual_direct_drive_samples_aliased"])

    def test_fine_grid_reveals_four_hypothetical_orientations_not_real_spoke_motion(self):
        r=analyze(["0","1/64","1/32","3/64","1/16"])
        self.assertFalse(r["counterfactual_direct_drive_samples_aliased"])
        self.assertEqual(r["counterfactual_direct_drive_unique_spoke_set_orientations"],4)
        self.assertEqual(r["counterfactual_direct_drive_spoke_phase_modulo_45_degrees"],
                         ["0","45/4","45/2","135/4","0"])
        self.assertEqual(r["canonical_rim_unique_spoke_set_orientations"],1)

    def test_exact_counterfactual_spoke_period(self):
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
