"""ROM-free tests for source-shape-only ART-4K heldout family selection."""
import copy
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/art/select_original_racer_heldout_roles.py"
spec = importlib.util.spec_from_file_location("source_split_selection", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def example():
    return {
        "schema": mod.OUTPUT_SCHEMA,
        "source_rom_sha256": mod.CANONICAL_ROM_SHA,
        "corpus_manifest_sha256": "d"*64,
        "split_request_sha256": "e"*64,
        "verified_distinct_original_binary_silhouettes": 3,
        "no_original_binary_silhouette_across_roles": True,
        "source_family_split_is_frozen_by_exact_input_hashes": True,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
        "withheld_candidate_is_an_independent_3d_camera": False,
        "total_source_windows": 4,
        "role_summary": {
            "fit": {"window_count": 0},
            "withheld_candidate": {"window_count": 0},
            "diagnostic": {"window_count": 4}},
        "connected_window_components": [
            {"windows": [mod.FIRST, "same-original-shape-window"],
             "role": "diagnostic", "source_binary_mask_shas": ["a"*64],
             "unique_source_binary_silhouette_count": 1},
            {"windows": ["genuinely-distinct-a"],
             "role": "diagnostic", "source_binary_mask_shas": ["b"*64],
             "unique_source_binary_silhouette_count": 1},
            {"windows": ["genuinely-distinct-b"],
             "role": "diagnostic", "source_binary_mask_shas": ["c"*64],
             "unique_source_binary_silhouette_count": 1}
        ],
    }


class HeldoutChoiceTests(unittest.TestCase):
    def test_all_shared_first_source_shapes_remain_fit(self):
        roles = mod.select_roles(example())
        self.assertEqual(roles["schema"], mod.REQUEST_SCHEMA)
        self.assertEqual(roles["roles"], {
            "first-1205-1220": "fit",
            "same-original-shape-window": "fit",
            "genuinely-distinct-a": "withheld_candidate",
            "genuinely-distinct-b": "withheld_candidate"})

    def test_split_policy_independent_of_component_order(self):
        original = example()
        backward = copy.deepcopy(original)
        backward["connected_window_components"].reverse()
        self.assertEqual(mod.select_roles(original), mod.select_roles(backward))

    def test_no_other_source_family_cannot_fake_holdout(self):
        report = example()
        report["connected_window_components"] = report["connected_window_components"][:1]
        report["total_source_windows"] = 2
        report["role_summary"]["diagnostic"]["window_count"] = 2
        with self.assertRaisesRegex(ValueError, "holdout"):
            mod.select_roles(report)

    def test_refuses_incorrect_status_and_approval(self):
        for field, replacement in (
            ("source_rom_sha256", "0"*64),
            ("no_original_binary_silhouette_across_roles", False),
            ("owner_likeness_approved", True),
            ("shipping_art_approved", True),
            ("withheld_candidate_is_an_independent_3d_camera", True),
        ):
            report = example()
            report[field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                mod.select_roles(report)

    def test_refuses_duplicate_windows_and_forged_shape_counts(self):
        report = example()
        report["connected_window_components"][1]["windows"].append(mod.FIRST)
        with self.assertRaises(ValueError):
            mod.select_roles(report)
        report = example()
        report["connected_window_components"][2]["unique_source_binary_silhouette_count"] = 2
        with self.assertRaises(ValueError):
            mod.select_roles(report)

    def test_rejects_cross_component_mask_leak_and_missing_source_sha(self):
        report = example()
        report["connected_window_components"][1]["source_binary_mask_shas"] = ["a"*64]
        with self.assertRaisesRegex(ValueError, "leaking"):
            mod.select_roles(report)
        report = example()
        report["corpus_manifest_sha256"] = "0"
        with self.assertRaisesRegex(ValueError, "immutable input SHA"):
            mod.select_roles(report)
        report = example()
        report["verified_distinct_original_binary_silhouettes"] = 4
        with self.assertRaises(ValueError):
            mod.select_roles(report)

    def test_refuses_preselected_model_influenced_fit(self):
        report = example()
        report["connected_window_components"][1]["role"] = "fit"
        with self.assertRaisesRegex(ValueError, "diagnostic"):
            mod.select_roles(report)


if __name__ == "__main__":
    unittest.main()
