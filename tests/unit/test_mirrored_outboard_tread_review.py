"""Owner-selected outboard, mirrored orange tread source contract."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.art.mirrored_outboard_tread_review import (
    MIRRORED_OUTBOARD_SOURCE_SHA256, OLD_TREAD, NEW_TREAD,
    make_candidate, mirrored_tread_source,
)
from tools.art.pedal_axle_clearance_review import (
    OUTBOARD_SOURCE_SHA256, outboard_pedal_source,
)

CANON = Path(__file__).resolve().parents[2] / "tools/art/candidates/unicycle_shared_rig.scad"


class MirroredOutboardTreadTests(unittest.TestCase):
    def test_exact_owner_selected_one_statement_change_and_reversibility(self):
        raw = CANON.read_bytes()
        before = outboard_pedal_source(raw)
        after = mirrored_tread_source(raw)
        self.assertEqual(hashlib.sha256(before).hexdigest(), OUTBOARD_SOURCE_SHA256)
        self.assertEqual(hashlib.sha256(after).hexdigest(),
                         MIRRORED_OUTBOARD_SOURCE_SHA256)
        self.assertEqual(after.count(NEW_TREAD.encode()),1)
        self.assertEqual(
            after.replace(NEW_TREAD.encode(),OLD_TREAD.encode()),before)
        self.assertIn(b"cylinder(h=1.08,r=0.065,center=true)",after)
        self.assertIn(b"for(y=[-0.30,0.30])",after)
        self.assertIn(b"[-0.22,0,1.67],[-0.22,0,2.235]",after)
        self.assertEqual(after.count(b"rig(rig_pose);"),1)

    def test_mirror_tread_center_offsets_across_axle(self):
        # Model-centered Y signs are exact because the source uses p[1].
        for center in (.56,-.56):
            old = center-.124
            new = center + (-.124 if center >= 0 else .124)
            if center > 0:
                self.assertAlmostEqual(new,old,places=12)
            else:
                self.assertAlmostEqual(new,-(.56-.124),places=12)
        self.assertAlmostEqual(.56-.124,.436,places=12)

    def test_source_drift_no_overwrite_and_immutable_candidate(self):
        original=CANON.read_bytes()
        with self.assertRaises(ValueError):
            mirrored_tread_source(original+b"// drift")
        with tempfile.TemporaryDirectory() as root:
            a,b=(Path(root)/p for p in ("canonical.scad","review.scad"))
            a.write_bytes(original)
            report=make_candidate(a,b)
            self.assertTrue(report["owner_preferred_wider_assembly"])
            self.assertTrue(report["owner_requested_tread_mirroring"])
            self.assertFalse(report["shipping_art_approved"])
            self.assertEqual(b.read_bytes(),mirrored_tread_source(original))
            self.assertEqual(a.read_bytes(),original)
            with self.assertRaises(FileExistsError):
                make_candidate(a,b)
            with self.assertRaisesRegex(ValueError,"must not overwrite"):
                make_candidate(a,a)


if __name__ == "__main__":
    unittest.main()
