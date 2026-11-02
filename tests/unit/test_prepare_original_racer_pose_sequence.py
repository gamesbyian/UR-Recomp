"""ROM-free adversarial source/pose evidence join checks."""
import copy
import unittest
from tools.art.prepare_original_racer_pose_sequence import build_input, POSES, CANONICAL_ROM_SHA

H, J = "a"*64, "b"*64


class OriginalPoseBinderTests(unittest.TestCase):
    def fixture(self):
        corpus = {
            "source_rom_sha256": CANONICAL_ROM_SHA,
            "source_rom_verified_and_used_for_composition": True,
            "registered_source_windows": ["first", "later"],
            "source_representations": {
                "a": {"player": "p1", "source_binary_mask_sha256": H},
                "b": {"player": "p2", "source_binary_mask_sha256": H},
                "c": {"player": "p1", "source_binary_mask_sha256": J}},
            "source_temporal_frame_observations": [
                {"window": "first", "guest_frame": 1205, "representations": {"p1": "a", "p2": "b"}},
                {"window": "first", "guest_frame": 1206, "representations": {"p1": "a"}},
                {"window": "later", "guest_frame": 1300, "representations": {"p1": "c"}}]}
        matrix = {
            "schema": "UR-RACER-UNPAIRED-POSE-SIMILARITY-MATRIX/1",
            "source_original_rom_sha256": CANONICAL_ROM_SHA,
            "camera_status": "provisional", "camera_shared_across_all_comparisons": True,
            "similarities_are_unpaired_hypotheses_not_source_pose_mapping": True,
            "per_pair_auto_alignment": False, "registration_mode": "fixed-witness",
            "camera_manifest_sha256": "c"*64,
            "viewer_five_pose_glb_sha256": {p: "d"*64 for p in POSES},
            "unique_original_binary_silhouettes": 2,
            "rows": [{"source_binary_mask_sha256": sha,
                      "unpaired_pose_scores": {p: {"mask_iou": value} for p in POSES}}
                     for sha, value in [(H, .5), (J, .3)]]}
        return corpus, matrix

    def test_authentic_frame_player_and_mask_join(self):
        corpus, matrix = self.fixture()
        result = build_input(corpus, matrix, ["first"], corpus_sha="f"*64)
        self.assertEqual([(r["player"], r["guest_frame"]) for r in result["frames"]],
                         [("p1", 1205), ("p1", 1206), ("p2", 1205)])
        self.assertEqual(result["frames"][0]["costs"]["upright"], .5)
        self.assertEqual(result["provenance"]["window_roles"]["first"], "unfrozen_diagnostic")

    def test_missing_original_mask_is_error_not_omission(self):
        corpus, matrix = self.fixture()
        matrix["rows"] = matrix["rows"][:1]
        matrix["unique_original_binary_silhouettes"] = 1
        with self.assertRaises(ValueError):
            build_input(corpus, matrix, ["later"])

    def test_bad_source_or_camera_provenance(self):
        for field, bad in [
                ("source_original_rom_sha256", "0"*64),
                ("per_pair_auto_alignment", True),
                ("camera_shared_across_all_comparisons", False),
                ("registration_mode", "automatically-zoomed")]:
            corpus, matrix = self.fixture()
            matrix[field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_input(corpus, matrix, ["first"])

    def test_wrong_player_and_duplicate_frame(self):
        for kind in ("wrong-player", "duplicate"):
            corpus, matrix = self.fixture()
            if kind == "wrong-player":
                corpus["source_representations"]["b"]["player"] = "p1"
            else:
                corpus["source_temporal_frame_observations"].append(
                    copy.deepcopy(corpus["source_temporal_frame_observations"][0]))
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                build_input(corpus, matrix, ["first"])

    def test_frozen_window_role_and_stale_hash(self):
        corpus, matrix = self.fixture()
        split = {
            "schema": "UR-RACER-FROZEN-SOURCE-FAMILY-SPLIT/1",
            "source_rom_sha256": CANONICAL_ROM_SHA,
            "corpus_manifest_sha256": "f"*64,
            "no_original_binary_silhouette_across_roles": True,
            "connected_window_components": [
                {"windows": ["first"], "role": "fit"},
                {"windows": ["later"], "role": "withheld_candidate"}]}
        self.assertEqual(build_input(corpus, matrix, ["later"], split, "f"*64)
                         ["provenance"]["window_roles"]["later"], "withheld_candidate")
        split["corpus_manifest_sha256"] = "0"*64
        with self.assertRaises(ValueError):
            build_input(corpus, matrix, ["later"], split, "f"*64)

    def test_fake_split_claim_cannot_cross_same_source_mask(self):
        corpus, matrix = self.fixture()
        corpus["source_representations"]["c"]["source_binary_mask_sha256"] = H
        split = {
            "schema": "UR-RACER-FROZEN-SOURCE-FAMILY-SPLIT/1",
            "source_rom_sha256": CANONICAL_ROM_SHA,
            "corpus_manifest_sha256": "f"*64,
            "no_original_binary_silhouette_across_roles": True,
            "connected_window_components": [
                {"windows": ["first"], "role": "fit"},
                {"windows": ["later"], "role": "withheld_candidate"}]}
        with self.assertRaises(ValueError):
            build_input(corpus, matrix, ["first"], split, "f"*64)


if __name__ == "__main__":
    unittest.main()
