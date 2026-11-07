"""Source-locked 2026 pedal/axle review: no new production rig or art approval."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.art.pedal_axle_clearance_review import (
    OUTBOARD_SOURCE_SHA256, PATCHES, continuous_clearance_bounds,
    outboard_pedal_source, make_candidate,
)
from tools.art.rounded_fork_clearance_review import (
    clearance_repaired_fork_source,
)

CANON = Path(__file__).resolve().parents[2] / "tools/art/candidates/unicycle_shared_rig.scad"


class OutboardPedalSourceTests(unittest.TestCase):
    def test_exact_source_reversible_patch_keeps_existing_four_other_parts(self):
        raw = CANON.read_bytes()
        old = clearance_repaired_fork_source(raw)
        candidate = outboard_pedal_source(raw)
        self.assertEqual(hashlib.sha256(candidate).hexdigest(), OUTBOARD_SOURCE_SHA256)
        restored = candidate.decode()
        for before, after in PATCHES:
            self.assertEqual(restored.count(after), 1)
            restored = restored.replace(after, before)
        self.assertEqual(restored.encode(), old)
        self.assertEqual(candidate.count(b"rig(rig_pose);"), 1)
        self.assertIn("[-0.22,0,1.67],[-0.22,0,2.235]", candidate.decode())
        self.assertIn("for(y=[-0.30,0.30])", candidate.decode())
        self.assertIn("cylinder(h=1.08,r=0.065,center=true)", candidate.decode())

    def test_continuous_360_degree_bound_conservatively_clears_blue_fork(self):
        result = continuous_clearance_bounds(.404)
        self.assertGreater(result[
            "continuous_fork_vs_all_pedal_material_y_gap_lower_bound"], .015)
        self.assertGreater(result["continuous_tire_radial_gap_lower_bound"], .14)
        self.assertGreater(result["continuous_inner_rim_radial_gap_lower_bound"], .04)
        self.assertTrue(result["symmetric_crank_base_overlaps_axle_extension"])
        self.assertFalse(result["intended_axle_crank_mating_independently_boolean_verified"])
        self.assertFalse(result["original_1994_mechanical_design_recovered"])

    def test_shrunken_fork_clearance_not_earned_by_sample_results(self):
        result = continuous_clearance_bounds(.45)
        self.assertLess(result[
            "continuous_fork_vs_all_pedal_material_y_gap_lower_bound"], 0)
        with self.assertRaises(ValueError):
            continuous_clearance_bounds(float("nan"))
        with self.assertRaises(ValueError):
            continuous_clearance_bounds(-1)

    def test_source_drift_and_no_overwrite(self):
        original = CANON.read_bytes()
        with self.assertRaises(ValueError):
            outboard_pedal_source(original + b"\n// unreviewed axle")
        with tempfile.TemporaryDirectory() as temp:
            a, b = (Path(temp) / name for name in ("canonical.scad", "candidate.scad"))
            a.write_bytes(original)
            receipt = make_candidate(a, b)
            self.assertEqual(b.read_bytes(), outboard_pedal_source(original))
            self.assertEqual(a.read_bytes(), original)
            self.assertEqual(receipt["candidate_scad_sha256"], OUTBOARD_SOURCE_SHA256)
            self.assertFalse(receipt["owner_likeness_approved"])
            with self.assertRaises(FileExistsError):
                make_candidate(a, b)
            with self.assertRaisesRegex(ValueError, "cannot overwrite"):
                make_candidate(a, a)


if __name__ == "__main__":
    unittest.main()
