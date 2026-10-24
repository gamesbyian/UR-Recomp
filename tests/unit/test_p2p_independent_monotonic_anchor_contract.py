"""Offline contract tests; deliberately not a trusted anchor implementation."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "p2p"))
import independent_monotonic_anchor_contract as c

class MonotonicAnchorContract(unittest.TestCase):
    def test_matching_positive_revisions_only(self):
        for revision in (1, 2, 100):
            self.assertTrue(c.adjudicate(revision,revision)["admit"])

    def test_rollback_and_unanchored_future_refuse(self):
        self.assertEqual(c.adjudicate(1,3)["reason"],"checkpoint rollback")
        self.assertEqual(c.adjudicate(4,3)["reason"],"unanchored future checkpoint")

    def test_missing_anchor_or_checkpoint_refuses(self):
        for kwargs in ({"checkpoint_present":False}, {"trusted_anchor_present":False}):
            self.assertFalse(c.adjudicate(3,3,**kwargs)["admit"])

    def test_bool_float_and_invalid_revision_refused(self):
        for a,b in ((True,1),(1,True),(1.0,1),(1,1.0),(0,0),(-1,-1),(None,1)):
            with self.subTest(a=a,b=b):
                self.assertFalse(c.adjudicate(a,b)["admit"])

    def test_joint_rollback_undetectable_without_anchor_independence(self):
        self.assertTrue(c.adjudicate(1,1)["admit"])
        report=c.report()
        self.assertFalse(report["anchor_implementation_exists"])
        self.assertFalse(report["authenticated_signature_proof"])
        self.assertFalse(report["production_network_tested"])
        self.assertEqual(report["release_gate_credit"],0)

    def test_uint64_overflow_refused_even_if_both_anchors_match(self):
        for checkpoint, trusted in ((2**64,2**64), (2**64,1),
                                    (1,2**64), (2**128,2**128)):
            with self.subTest(checkpoint=checkpoint,trusted=trusted):
                self.assertFalse(c.adjudicate(checkpoint,trusted)["admit"])
        self.assertTrue(c.adjudicate(2**64-1,2**64-1)["admit"])

if __name__=="__main__":
    unittest.main()
