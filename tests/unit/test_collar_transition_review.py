"""Owner-directed 2026 collar: exact-source and unchanged-art contracts."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.art.collar_transition_review import (
    BASELINE_SOURCE_SHA256, OLD, NEW, sculpt, make_candidate,
)
from tools.art.export_articulated_unicycle import (
    PARTS, POSES, source_without_entrypoint, saddle_mount_from_source,
)
from tools.art.scad_materials import materials_for_part

SOURCE=Path(__file__).resolve().parents[2]/"tools/art/candidates/unicycle_shared_rig.scad"


class OwnerDirectedCollarTests(unittest.TestCase):
    def test_source_locked_one_change_in_existing_rig(self):
        original=SOURCE.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),BASELINE_SOURCE_SHA256)
        changed=sculpt(original)
        self.assertNotEqual(original,changed)
        self.assertEqual(changed.decode().replace(NEW,OLD),original.decode())
        self.assertIn("rig(rig_pose);",changed.decode())
        self.assertEqual(len(PARTS),5)
        self.assertEqual(len(POSES),5)
        self.assertEqual(saddle_mount_from_source(original.decode()),
                         saddle_mount_from_source(changed.decode()))
        self.assertTrue(source_without_entrypoint(changed.decode()))
        for name in PARTS:
            self.assertEqual(len(materials_for_part(original.decode(),name)),
                             len(materials_for_part(changed.decode(),name)))

    def test_symmetric_lateral_collar_and_exposed_seatpost(self):
        self.assertIn("translate([-0.22,0,1.93])",NEW)
        self.assertIn("translate([-0.22,0,2.003])",NEW)
        # All new mechanical primitive centers are exactly on Y=0.
        self.assertNotIn("translate([-0.22,0.2",NEW)
        self.assertIn("[-0.20,0,2.24]",NEW)
        self.assertIn("[-0.22,0,1.89]",NEW)
        self.assertIn("h=0.13,r1=0.16,r2=0.14",NEW)
        self.assertNotIn("rim_and_hub()",NEW)
        self.assertNotIn("saddle_section(",NEW)

    def test_changed_source_rejected_no_output_overwrite(self):
        original=SOURCE.read_bytes()
        with self.assertRaisesRegex(ValueError,"source SHA changed"):
            sculpt(original+b"\n")
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"input.scad"
            dst=Path(d)/"new.scad"
            src.write_bytes(original)
            receipt=make_candidate(src,dst)
            self.assertEqual(dst.read_bytes(),sculpt(original))
            self.assertEqual(src.read_bytes(),original)
            self.assertFalse(receipt["owner_likeness_approved"])
            with self.assertRaises(FileExistsError):
                make_candidate(src,dst)
            with self.assertRaisesRegex(ValueError,"overwrite canonical"):
                make_candidate(src,src)


if __name__=="__main__":
    unittest.main()
