"""Owner-directed single-rig fork/shoulder study: source-exact art safety."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.art.collar_transition_review import sculpt,assert_seatpost_aligned
from tools.art.rounded_fork_clearance_review import (
    OLD_LOOP,NEW_LOOP,OLD_SHOULDER,NEW_SHOULDER,
    STRAIGHT_SOURCE_SHA256,PROPOSED_SOURCE_SHA256,REPAIRED_SOURCE_SHA256,
    REPAIRED_LOOP,rounded_fork_source,clearance_repaired_fork_source,make_candidate
)

SRC=Path(__file__).resolve().parents[2]/"tools/art/candidates/unicycle_shared_rig.scad"


class RoundedForkReviewTests(unittest.TestCase):
    def test_source_locked_continuity_and_preservation(self):
        raw=SRC.read_bytes()
        straight=sculpt(raw)
        self.assertEqual(hashlib.sha256(straight).hexdigest(),STRAIGHT_SOURCE_SHA256)
        rounded=rounded_fork_source(raw)
        self.assertEqual(hashlib.sha256(rounded).hexdigest(),PROPOSED_SOURCE_SHA256)
        self.assertEqual(rounded.decode().replace(NEW_LOOP,OLD_LOOP)
                         .replace(NEW_SHOULDER,OLD_SHOULDER),straight.decode())
        self.assertEqual(rounded.count(b"rig(rig_pose);"),1)
        assert_seatpost_aligned(rounded.decode())
        self.assertIn("for(y=[-0.28,0.28])",rounded.decode())
        repaired=clearance_repaired_fork_source(raw)
        self.assertEqual(hashlib.sha256(repaired).hexdigest(),REPAIRED_SOURCE_SHA256)
        self.assertEqual(repaired.decode().replace(REPAIRED_LOOP,NEW_LOOP),rounded.decode())
        self.assertEqual(repaired.count(b"rig(rig_pose);"),1)
        assert_seatpost_aligned(repaired.decode())
        self.assertIn("y*0.50,1.42],0.105,0.16",rounded.decode())
        self.assertIn("[-0.22,0,1.67],[-0.22,0,2.235]",rounded.decode())
        # No new rim/hub/shaft/camera/posed fallback module.
        for module in ("saddle(", "pedals(", "rim_and_hub(", "tire("):
            self.assertEqual(straight.count(module.encode()),rounded.count(module.encode()))

    def test_bad_source_and_overwrite_fail_closed(self):
        original=SRC.read_bytes()
        with self.assertRaises(ValueError):
            rounded_fork_source(original+b"\n// surprise")
        with tempfile.TemporaryDirectory() as root:
            source=Path(root)/"canonical.scad"
            target=Path(root)/"candidate.scad"
            source.write_bytes(original)
            receipt=make_candidate(source,target)
            self.assertEqual(target.read_bytes(),clearance_repaired_fork_source(original))
            self.assertEqual(receipt["candidate_scad_sha256"],REPAIRED_SOURCE_SHA256)
            self.assertEqual(receipt["historical_sampled_only_scad_sha256"],PROPOSED_SOURCE_SHA256)
            self.assertEqual(source.read_bytes(),original)
            self.assertFalse(receipt["owner_likeness_approved"])
            with self.assertRaises(FileExistsError):
                make_candidate(source,target)
            with self.assertRaisesRegex(ValueError,"cannot replace"):
                make_candidate(source,source)


if __name__=="__main__":
    unittest.main()
