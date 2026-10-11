"""Adversarial strict original native 2P post-GO source-pair characterizations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_2p_postgo_source_pairs import (
    compare, assess, WIDTH, HEIGHT, FRAME,
)
from tools.check_baldosa_wide_single_slot_source import HEADER, read_source


class OriginalPostGoPairedObjSourceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("baldosa-ws342-captures", "baldosa-ws342-obj-slots",
                          "baldosa-evidence"):
            (self.root / directory).mkdir()
        self.original = bytes((8, 15, 24, 0)) * (WIDTH * HEIGHT)
        self.sources = {slot: bytearray(WIDTH * HEIGHT * 4)
                        for slot in (96, 97, 98, 99)}
        for upper, lower, x, rgb in (
            (98, 97, 125, (247, 165, 140)),
            (99, 96, 148, (49, 181, 33)),
        ):
            self.paint(self.sources[upper], x, 70, (*rgb, 255))
            self.paint(self.sources[upper], x + 1, 78, (*rgb, 255))
            self.paint(self.sources[lower], x - 13, 182, (*rgb, 255))
            self.paint(self.sources[lower], x - 12, 190, (*rgb, 255))
        self.flush()

    @staticmethod
    def paint(data, x, y, rgba):
        p = (y * WIDTH + x) * 4
        data[p:p + 4] = bytes(rgba)

    def src(self, slot):
        return (self.root / "baldosa-ws342-obj-slots" /
                f"ur-baldosa-ws342-obj-slot{slot}-frame{FRAME:06d}.pam")

    def source_report(self, slot):
        return (self.root / "baldosa-evidence" /
                f"ws342_obj_slot_{slot}_frame{FRAME}.json")

    def flush(self):
        (self.root / "baldosa-ws342-captures" /
         f"ur-baldosa-ws342-{FRAME:06d}.pam").write_bytes(
             HEADER + self.original)
        sha = hashlib.sha256(self.original).hexdigest()
        for slot in (96, 97, 98, 99):
            self.src(slot).write_bytes(HEADER + self.sources[slot])
            metadata = read_source(self.src(slot), slot)
            self.source_report(slot).write_text(json.dumps({
                "schema_version": 1,
                "status": "passed",
                "source_log_matches_pam": True,
                "identical_complete_original_342_rasters": 7,
                "minimum_shared_frames": 7,
                "shared_full_frame_guest_ids": [
                    1808, 1824, 1840, 1856, 1872, 1888, 2208,
                ],
                "differing_original_rasters": [],
                "source": metadata,
                "source_frame_main_raster_sha256": sha,
                "guest_crc_comparison":
                    "Externally enforced byte-exact in native workflow",
            }), encoding="utf-8")

    def test_two_exact_rgba_source_aliases_on_genuine_registered_pixels(self):
        report = assess(self.root)
        self.assertEqual(report["guest_frame"], 2208)
        self.assertEqual(sorted(report["source_paired_upper_to_lower"]),
                         ["98->97", "99->96"])
        for record in report["source_paired_upper_to_lower"].values():
            self.assertEqual(record["status"],
                             "source-positive-exact-translated-rgba-alias")
            self.assertEqual(record["upper_source_opaque_pixels"], 2)
            self.assertEqual(record["lower_source_opaque_pixels"], 2)
            self.assertEqual(record["different_rgba_after_registration"], 0)
            self.assertTrue(record["exact_rgba_split_alias_observed"])
            self.assertEqual(record["bbox_inferred_upper_to_lower_translation_xy"],
                             [-13, 112])
        self.assertTrue(report["postgo_translation_same_across_both_player_pairs"])
        self.assertEqual(report["original_prerace_source_translation_xy_not_assumed"],
                         [0, 113])
        self.assertFalse(report["remastered_source_erasure_allowed"])

    def test_colour_divergence_is_observed_without_falsely_failing_provenance(self):
        self.paint(self.sources[97], 112, 182, (9, 10, 11, 255))
        self.flush()
        report = assess(self.root)
        one = report["source_paired_upper_to_lower"]["98->97"]
        self.assertEqual(one["status"], "source-visible-split-divergence")
        self.assertEqual(one["different_alpha_after_registration"], 0)
        self.assertEqual(one["different_rgba_after_registration"], 1)
        self.assertEqual(one["bounded_differences"][0]["lower_xy"], [112, 182])
        self.assertTrue(report["result_is_observational_not_required_exact_alias"])

    def test_alpha_missing_in_lower_source_is_real_divergence(self):
        self.paint(self.sources[97], 113, 190, (0, 0, 0, 0))
        self.flush()
        record = assess(self.root)["source_paired_upper_to_lower"]["98->97"]
        self.assertEqual(record["different_alpha_registered_coordinates"], 1)
        self.assertFalse(record["exact_rgba_split_alias_observed"])

    def test_unpaired_upper_last_row_must_not_silently_pass_as_alias(self):
        self.paint(self.sources[98], 144, 111, (22, 22, 22, 255))
        self.flush()
        record = assess(self.root)["source_paired_upper_to_lower"]["98->97"]
        self.assertGreater(record["different_alpha_after_registration"], 0)
        self.assertEqual(record["status"], "source-visible-split-divergence")

    def test_source_empty_for_one_pair_is_legitimate_not_invented_rider(self):
        self.sources[98] = bytearray(WIDTH * HEIGHT * 4)
        self.sources[97] = bytearray(WIDTH * HEIGHT * 4)
        self.flush()
        record = assess(self.root)["source_paired_upper_to_lower"]["98->97"]
        self.assertEqual(record["status"], "source-empty")
        self.assertFalse(record["exact_rgba_split_alias_observed"])

    def test_old_countdown_shift_is_valid_as_input_not_postgo_assumption(self):
        # Rebuild the P1 lower plane with the old (0,+113) raster shift.
        # Exact source copy is measured, not forced to the later (-13,+112).
        lower = bytearray(WIDTH * HEIGHT * 4)
        upper = self.sources[98]
        for x, y in ((125, 70), (126, 78)):
            at = 4 * (y * WIDTH + x)
            self.paint(lower, x, y + 113, tuple(upper[at:at + 4]))
        self.sources[97] = lower
        self.flush()
        report = assess(self.root)
        one = report["source_paired_upper_to_lower"]["98->97"]
        self.assertTrue(one["exact_rgba_split_alias_observed"])
        self.assertEqual(one["bbox_inferred_upper_to_lower_translation_xy"],
                         [0, 113])
        self.assertFalse(report["postgo_translation_same_across_both_player_pairs"])

    def test_mismatched_source_viewport_geometry_is_reported_not_blessed(self):
        self.paint(self.sources[98], 130, 160, (20, 25, 30, 255))
        self.flush()
        record = assess(self.root)["source_paired_upper_to_lower"]["98->97"]
        self.assertEqual(record["upper_source_in_lower_analytic_half"], 1)
        self.assertFalse(record["exact_rgba_split_alias_observed"])

    def test_true_pair_specific_translations_do_not_get_falsely_conflated(self):
        # P1 alone shifts one more pixel right, preserving its *own*
        # exact alias but no longer sharing P2's observed transform.
        old = self.sources[97]
        source = bytearray(WIDTH * HEIGHT * 4)
        for x, y in ((112, 182), (113, 190)):
            at = 4 * (y * WIDTH + x)
            self.paint(source, x + 1, y, tuple(old[at:at + 4]))
        self.sources[97] = source
        self.flush()
        report = assess(self.root)
        self.assertTrue(report["source_paired_upper_to_lower"]
                        ["98->97"]["exact_rgba_split_alias_observed"])
        self.assertFalse(report["postgo_translation_same_across_both_player_pairs"])

    def test_invalid_cross_raster_size_fails(self):
        with self.assertRaisesRegex(ValueError, "complete"):
            compare(self.sources[98][:-4], self.sources[97])

    def test_changed_unmodified_original_stock_rejects_source_attestation(self):
        self.original = bytes([0]) + self.original[1:]
        (self.root / "baldosa-ws342-captures" /
         f"ur-baldosa-ws342-{FRAME:06d}.pam").write_bytes(
             HEADER + self.original)
        with self.assertRaisesRegex(ValueError, "unproven"):
            assess(self.root)

    def test_forged_past_seven_frames_or_lost_postgo_record_rejected(self):
        report = json.loads(self.source_report(99).read_text())
        report["shared_full_frame_guest_ids"] = [
            1808, 1824, 1840, 1856, 1872, 1888, 1904]
        self.source_report(99).write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unproven"):
            assess(self.root)

    def test_source_metadata_SHA_forgery_rejected(self):
        report = json.loads(self.source_report(96).read_text())
        report["source"]["source_sha256"] = "0" * 64
        self.source_report(96).write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "slot96"):
            assess(self.root)

    def test_mixed_slot_from_different_source_raster_rejected(self):
        self.src(98).write_bytes(self.src(99).read_bytes())
        with self.assertRaisesRegex(ValueError, "slot98"):
            assess(self.root)


if __name__ == "__main__":
    unittest.main()
