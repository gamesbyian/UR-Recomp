"""The 2026 owner silhouette remains unchanged by optional shaft-parent repair."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.art.rotating_axle_bearing_review import (
    rotating_axle_source, generate, PATCHES, ROTATING_AXLE_SOURCE_SHA256,
    SHAFT_RADIUS, BORE_RADIUS, BORE_FN, MIN_CLEARANCE,
)
from tools.art.mirrored_outboard_tread_review import mirrored_tread_source

SOURCE=Path(__file__).resolve().parents[2]/"tools/art/candidates/unicycle_shared_rig.scad"


class OwnerRotatingAxleSourceTests(unittest.TestCase):
    def test_only_three_reversible_source_spans_and_owner_mirroring(self):
        canonical=SOURCE.read_bytes()
        prior=mirrored_tread_source(canonical)
        after=rotating_axle_source(canonical)
        self.assertEqual(hashlib.sha256(after).hexdigest(),ROTATING_AXLE_SOURCE_SHA256)
        for old,new in PATCHES:
            self.assertEqual(after.count(new.encode()),1)
            self.assertNotIn(old.encode(),after)
            after=after.replace(new.encode(),old.encode())
        self.assertEqual(after,prior)
        source=rotating_axle_source(canonical).decode()
        self.assertIn("p1=[0.31*cos(phase),0.56,0.31*sin(phase)];",source)
        self.assertIn("p2=[-0.31*cos(phase),-0.56,-0.31*sin(phase)];",source)
        self.assertIn("p[1]>=0?-0.124:0.124",source)
        self.assertIn("[-0.22,0,1.67],[-0.22,0,2.235]",source)
        self.assertIn("for(y=[-0.30,0.30])",source)
        self.assertIn("cylinder(h=1.08,r=0.065,center=true)",source)
        self.assertIn("cylinder(h=1.08+0.02,r=0.071,center=true,$fn=80)",source)
        self.assertIn("cylinder(h=0.56+0.02,r=0.071,center=true,$fn=80)",source)
        self.assertEqual(source.count("rig(rig_pose);"),1)

    def test_explicit_radial_gap_rejects_source_impossible_clearance(self):
        self.assertAlmostEqual(SHAFT_RADIUS,.065)
        self.assertAlmostEqual(BORE_RADIUS,.071)
        self.assertEqual(BORE_FN,80)
        self.assertGreater(MIN_CLEARANCE,.005)
        self.assertLess(MIN_CLEARANCE,.00601)

    def test_no_overwrite_or_unknown_canonical_and_exact_signals(self):
        canonical=SOURCE.read_bytes()
        with self.assertRaises(ValueError):
            rotating_axle_source(canonical+b"\n// drift")
        with tempfile.TemporaryDirectory() as root:
            origin,option=(Path(root)/name for name in ("canonical.scad","bored.scad"))
            origin.write_bytes(canonical)
            report=generate(origin,option)
            self.assertEqual(origin.read_bytes(),canonical)
            self.assertEqual(option.read_bytes(),rotating_axle_source(canonical))
            self.assertEqual(report["shaft_parent"],"pedals")
            self.assertEqual(report["bearing_and_bored_lower_fork_parent"],"fork_and_frame")
            self.assertTrue(report["owner_preferred_wider_spacing_and_mirrored_tread_preserved"])
            self.assertFalse(report["actual_GLb_surface_clearance_proved_by_source_generator"])
            self.assertFalse(report["original_1994_bearing_or_axle_mechanics_recovered"])
            self.assertFalse(report["shipping_art_approved"])
            with self.assertRaises(FileExistsError):
                generate(origin,option)
            with self.assertRaisesRegex(ValueError,"refusing to overwrite"):
                generate(origin,origin)


if __name__=="__main__":
    unittest.main()
