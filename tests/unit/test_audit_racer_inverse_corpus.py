"""ROM-free adversarial coverage for the inverse corpus registry audit."""
import copy
import hashlib
import json
import unittest
from pathlib import Path

from tools.art.audit_racer_inverse_corpus import audit, DEFAULT, SCHEMA


class RacerInverseCorpusAuditTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def run_audit(self):
        return audit(self.data, hashlib.sha256(b"test").hexdigest())

    def test_current_registry_is_referentially_sound(self):
        result = self.run_audit()
        self.assertEqual(result["schema"], SCHEMA)
        self.assertGreater(result["sequence_count"], 1)
        self.assertEqual(result["registered_entry_count"], len(self.data["entries"]))
        self.assertFalse(result["heldout_pose_family_independently_verified"])
        self.assertFalse(result["shipping_art_approved"])
        self.assertTrue(all(not g["eligible_for_authentic_3d_holdout"] for g in result["groups"]))

    def test_duplicate_representation_rejected(self):
        self.data["entries"].append(copy.deepcopy(self.data["entries"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.run_audit()

    def test_unknown_representation_rejected(self):
        self.data["motion_review_sequence"]["frames"][0]["p1_representation_id"] = "invented"
        with self.assertRaisesRegex(ValueError, "unknown"):
            self.run_audit()

    def test_cross_player_identity_rejected(self):
        f = self.data["motion_review_sequence"]["frames"][0]
        f["p1_representation_id"] = f["p2_representation_id"]
        with self.assertRaisesRegex(ValueError, "wrong-player"):
            self.run_audit()

    def test_out_of_order_frame_rejected(self):
        frames = self.data["motion_review_sequence"]["frames"]
        frames[1]["frame"] = frames[0]["frame"]
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            self.run_audit()

    def test_range_mismatch_rejected(self):
        self.data["motion_review_sequence"]["window_end"] += 1
        with self.assertRaisesRegex(ValueError, "range"):
            self.run_audit()

    def test_false_bool_frame_rejected(self):
        self.data["motion_review_sequence"]["frames"][0]["frame"] = True
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            self.run_audit()


if __name__ == "__main__":
    unittest.main()
