"""Read-only QA-08 moving-wide source observations, never HD admission."""
from copy import deepcopy
import hashlib
import unittest

from tools.compare_baldosa_wide_obj_frames import compare, PAIRS, SLOTS


def digest(s):
    return hashlib.sha256(str(s).encode()).hexdigest()


def record(frame, *, later=False):
    slot_data = {}
    for slot in SLOTS:
        slot_data[slot] = {
            "source_opaque": 0, "source_opaque_top": 0,
            "source_opaque_bottom": 0, "unique_source_pixels": 0,
            "overlap_source_pixels": 0, "main_rgb_matches_source": 0,
            "main_rgb_differs_source": 0,
            "unique_main_rgb_differs": 0,
            "overlap_main_rgb_differs": 0,
        }
    if later:
        # Two emitted pixels on the later frame, but an RGB mismatch remains
        # an unresolved final-PUU-depth or color-processing candidate.
        slot_data["99"].update(
            source_opaque=2, source_opaque_top=2,
            unique_source_pixels=2, main_rgb_matches_source=1,
            main_rgb_differs_source=1, unique_main_rgb_differs=1,
        )
    else:
        slot_data["98"].update(
            source_opaque=3, source_opaque_top=3,
            unique_source_pixels=3, main_rgb_matches_source=3,
        )
        slot_data["99"].update(
            source_opaque=1, source_opaque_top=1,
            unique_source_pixels=1, main_rgb_matches_source=1,
        )
    return {
        "schema_version": 1,
        "status": "unproven" if later else "passed",
        "guest_frame": frame,
        "stock_ppu_sha256": digest(f"main:{frame}"),
        "source_obj_sha256": {slot: digest(f"{slot}:{frame}") for slot in SLOTS},
        "per_slot": slot_data,
        "source_overlap_pairs": {pair: 0 for pair in PAIRS},
        "source_alpha_total_across_slots": 2 if later else 4,
        "source_alpha_union_pixels": 2 if later else 4,
        "source_alpha_multi_slot_pixels": 0,
    }


class MovingSourceTests(unittest.TestCase):
    def test_source_absence_or_rgb_disagreement_is_observed_not_authorized(self):
        earlier, later = record(1856), record(1872, later=True)
        result = compare(earlier, later)
        self.assertEqual(result["status"], "observed-not-admitted")
        self.assertEqual(result["frames"], [1856, 1872])
        self.assertEqual(result["guest_frame_delta"], 16)
        self.assertEqual(result["slot_source_deltas"]["98"]["source_delta"], -3)
        self.assertTrue(result["slot_source_deltas"]["98"]["source_absent_after"])
        self.assertEqual(
            result["unresolved_per_slot_bg_window_or_priority_candidates"]["99"],
            [0, 1],
        )
        self.assertFalse(result["safe_to_destructively_replace_original_obj"])

    def test_comparison_rejects_false_temporal_and_provenance_claims(self):
        a, b = record(1856), record(1872, later=True)
        cases = [
            ("identical frame index", dict(guest_frame=1856),
             "ordered distinct guest frames"),
            ("backwards frame index", dict(guest_frame=1840),
             "ordered distinct guest frames"),
            ("unchanged original main raster", dict(
                stock_ppu_sha256=a["stock_ppu_sha256"]),
             "identical Original main raster"),
            ("wrong slot census", dict(per_slot={"98": b["per_slot"]["98"]}),
             "exactly four"),
            ("bad digest", dict(stock_ppu_sha256="f" * 3),
             "invalid source/main raster digest"),
            ("wrong total", dict(source_alpha_total_across_slots=300),
             "source-alpha sum"),
            ("invalid multisource union", dict(
                source_alpha_multi_slot_pixels=4),
             "invalid union"),
        ]
        for label, changes, message in cases:
            with self.subTest(label=label):
                invalid = deepcopy(b)
                invalid.update(changes)
                with self.assertRaisesRegex(ValueError, message):
                    compare(a, invalid)
        invalid = deepcopy(b)
        invalid["per_slot"]["99"]["main_rgb_differs_source"] = 50
        with self.assertRaisesRegex(ValueError, "inconsistent per-slot"):
            compare(a, invalid)

    def test_existing_source_slot_pair_overlap_delta(self):
        a, b = record(1856), record(1872, later=True)
        for item, count in ((a, 1), (b, 2)):
            # Two OAM slots contribute to exactly count common source pixels.
            # No final ownership is inferred from the matched RGB.
            item["per_slot"]["98"].update(
                source_opaque=count, source_opaque_top=count,
                unique_source_pixels=0, overlap_source_pixels=count,
                main_rgb_matches_source=count,
                main_rgb_differs_source=0,
            )
            item["per_slot"]["99"].update(
                source_opaque=count, source_opaque_top=count,
                unique_source_pixels=0, overlap_source_pixels=count,
                main_rgb_matches_source=0,
                main_rgb_differs_source=count,
                unique_main_rgb_differs=0,
                overlap_main_rgb_differs=count,
            )
            item["source_overlap_pairs"]["98-99"] = count
            item["source_alpha_total_across_slots"] = count * 2
            item["source_alpha_union_pixels"] = count
            item["source_alpha_multi_slot_pixels"] = count
        result = compare(a, b)
        self.assertEqual(result["source_pair_overlap_deltas"]["98-99"], {
            "before": 1, "after": 2, "delta": 1,
        })
        self.assertFalse(result["safe_to_destructively_replace_original_obj"])


if __name__ == "__main__":
    unittest.main()
