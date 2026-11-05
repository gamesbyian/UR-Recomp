"""Offline preflight negative controls; not a CI qualification suite."""
import unittest
from tools.ci_collective_candidate import validate_manifest


def fixture():
    return {
        "schema": 1, "batch_id": "UR-CI-PILOT-001",
        "base_sha": "a" * 40, "candidate_sha": "b" * 40,
        "members": [
            {"work_id": "UR-WIDE-07", "pr": 100, "head_sha": "c" * 40,
             "changed_paths": ["native/presentation/one.cpp"]},
            {"work_id": "UR-UI-08", "pr": 101, "head_sha": "d" * 40,
             "changed_paths": ["native/product/two.cpp"]},
        ],
    }


class TestCollectiveCandidate(unittest.TestCase):
    def test_coherent_proposal_not_qualification(self):
        result = validate_manifest(fixture())
        self.assertEqual(result["members"], 2)
        self.assertFalse(result["required_exact_candidate_tests_executed"])
        self.assertFalse(result["live_github_heads_and_diffs_verified"])

    def test_overlap_rejected(self):
        x = fixture()
        x["members"][1]["changed_paths"] = x["members"][0]["changed_paths"][:]
        with self.assertRaisesRegex(ValueError, "overlap"):
            validate_manifest(x)

    def test_duplicate_identity_rejected(self):
        for key in ("work_id", "pr", "head_sha"):
            with self.subTest(key=key):
                x = fixture()
                x["members"][1][key] = x["members"][0][key]
                with self.assertRaises(ValueError):
                    validate_manifest(x)

    def test_missing_and_unknown_keys_rejected(self):
        for key in ("candidate_sha", "members"):
            x = fixture()
            del x[key]
            with self.assertRaises(ValueError):
                validate_manifest(x)
        x = fixture()
        x["approved"] = True
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_invalid_source_sha_rejected(self):
        for value in (None, "abc", "A" * 40):
            with self.subTest(value=value):
                x = fixture()
                x["candidate_sha"] = value
                with self.assertRaises(ValueError):
                    validate_manifest(x)

    def test_noncanonical_paths_rejected(self):
        for path in ("../other", "/absolute", "a//b", "a/./b", "a\\b", ""):
            with self.subTest(path=path):
                x = fixture()
                x["members"][0]["changed_paths"] = [path]
                with self.assertRaises(ValueError):
                    validate_manifest(x)

    def test_incomplete_member_population_rejected(self):
        for count in (0, 1, 6):
            with self.subTest(count=count):
                x = fixture()
                x["members"] = x["members"][:1] * count
                with self.assertRaises(ValueError):
                    validate_manifest(x)

    def test_duplicate_path_within_member_rejected(self):
        x = fixture()
        x["members"][0]["changed_paths"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate path"):
            validate_manifest(x)


if __name__ == "__main__":
    unittest.main()
