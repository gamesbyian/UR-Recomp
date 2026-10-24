"""ROM-free source identity preflight; no patch, CI or release qualification."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from recovery_source_epoch_check import classify

A = "a" * 40
B = "b" * 40
C = "c" * 40
D = "d" * 40


def candidate(pre=None, post=None):
    return {"source_main_sha": A, "preimage_blob_shas": ({"tools/example.py": B} if pre is None else pre),
            "proposed_blob_shas": ({"tools/example.py": C} if post is None else post)}


def observed(current=None, main=C):
    return {"main_sha": main, "blob_shas": ({"tools/example.py": B} if current is None else current)}


class SourceEpoch(unittest.TestCase):
    def test_exact_preimage_survives_unrelated_main_advancement(self):
        r = classify(candidate(), observed())
        self.assertEqual(r["status"], "applicable-preimages")
        self.assertFalse(r["main_epoch_matches"])
        self.assertFalse(r["patch_tested"])
        self.assertFalse(r["release_gate_credit"])

    def test_exact_proposed_blob_already_integrated(self):
        self.assertEqual(classify(candidate(), observed({"tools/example.py": C}))["status"],
                         "already-proposed-blobs")

    def test_stale_conflicting_blob_refuses(self):
        r = classify(candidate(), observed({"tools/example.py": D}))
        self.assertEqual(r["status"], "source-conflict")

    def test_partial_integration_needs_review(self):
        pre = {"a.py": A, "b.py": B}
        post = {"a.py": C, "b.py": D}
        r = classify(candidate(pre, post), observed({"a.py": C, "b.py": B}))
        self.assertEqual(r["status"], "mixed-needs-review")

    def test_missing_or_extra_observed_path_refuses(self):
        for current in ({"other.py": B}, {"tools/example.py": B, "extra.py": A}):
            with self.subTest(current=current), self.assertRaisesRegex(ValueError, "exactly cover"):
                classify(candidate(), observed(current))

    def test_invalid_git_sha_and_path_refuse(self):
        for path in ("../escape.py", "/abs.py", "x//y", "x\\y", "bad\x7f.py"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                classify(candidate({path: B}, {path: C}), observed({path: B}))
        for sha in (True, "z" * 40, "A" * 40, "a" * 39):
            with self.subTest(sha=sha), self.assertRaises(ValueError):
                classify(candidate({"x": sha}), observed({"x": B}))

    def test_absent_file_can_be_a_valid_new_file_preimage(self):
        r = classify(candidate({"new.py": None}, {"new.py": C}),
                     observed({"new.py": None}))
        self.assertEqual(r["status"], "applicable-preimages")

    def test_no_invented_proposed_or_qa_status(self):
        r = classify(candidate(post={}), observed())
        self.assertEqual(r["files"][0]["status"], "preimage-match")
        self.assertFalse(r["release_gate_credit"])


if __name__ == "__main__":
    unittest.main()
