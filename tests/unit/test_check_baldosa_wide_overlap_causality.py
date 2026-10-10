"""Causal overlap diagnostics never infer a unique painter from identical RGB."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tools.check_baldosa_wide_overlap_causality import (
    classify, verify_native, correlate_authenticated_rear,
)
from tools.check_baldosa_wide_slot_final_visibility import WIDTH, HEIGHT


def pix(buf, x, y, r, g, b, a):
    i = (y * WIDTH + x) * 4
    buf[i:i+4] = bytes((r, g, b, a))


class NativeOverlapCausalityTests(unittest.TestCase):
    def setUp(self):
        self.stock = bytearray(bytes((9, 10, 11, 0)) * (WIDTH * HEIGHT))
        self.front = bytearray(WIDTH * HEIGHT * 4)
        self.rear = bytearray(WIDTH * HEIGHT * 4)
        self.no_front = bytearray(self.stock)
        self.no_pair = bytearray(self.stock)
        # One source-only front pixel. Its removal reveals other original.
        pix(self.front, 100, 40, 210, 30, 30, 255)
        pix(self.stock, 100, 40, 210, 30, 30, 0)
        pix(self.no_pair, 100, 40, 9, 10, 11, 0)
        # One true same-colour front/rear overlap with redundancy:
        # deleting front alone leaves the identical rear colour;
        # deleting BOTH reveals a different background.
        pix(self.front, 101, 40, 80, 50, 20, 255)
        pix(self.rear, 101, 40, 80, 50, 20, 255)
        pix(self.stock, 101, 40, 80, 50, 20, 0)
        pix(self.no_front, 101, 40, 80, 50, 20, 0)
        pix(self.no_pair, 101, 40, 9, 10, 11, 0)
        # A rear-only pixel must not be attributed to removing front.
        pix(self.rear, 102, 40, 60, 90, 100, 255)
        pix(self.stock, 102, 40, 60, 90, 100, 0)
        pix(self.no_front, 102, 40, 60, 90, 100, 0)
        pix(self.no_pair, 102, 40, 9, 10, 11, 0)
        self.no_front[100 * 4 + 40 * WIDTH * 4:100 * 4 + 40 * WIDTH * 4 + 4] = (
            bytes((9, 10, 11, 0)))
        self.d = [bytes(x) for x in
                  (self.stock, self.front, self.rear, self.no_front, self.no_pair)]

    def reports(self):
        s, f, r, nof, nop = self.d
        sha = lambda x: hashlib.sha256(x).hexdigest()
        single = {
            "status": "passed", "guest_frame": 1856, "source_oam_slot": 98,
            "guest_crc_equal_in_all_three_processes": True,
            "single_slot_original_ppu_removal_armed": True,
            "source_emitted_alpha_pixels": 2,
            "native_ppu_final_contributed_pixels": 1,
            "native_ppu_changed_outside_emitted_source_alpha": 0,
            "stock_sha256": sha(s), "source_sha256": sha(f),
            "counterfactual_sha256": sha(nof),
        }
        pair = {
            "status": "passed", "guest_frame": 1856,
            "removed_oam_slots": [98, 99],
            "guest_crc_equal_in_all_four_processes": True,
            "exact_pair_removal_armed": True,
            "source_alpha_union_pixels": 3,
            "source_alpha_pair_overlap_pixels": 1,
            "final_changed_pixels": 3,
            "changed_outside_source_union": 0,
            "stock_sha256": sha(s), "first_source_sha256": sha(f),
            "second_source_sha256": sha(r), "counterfactual_sha256": sha(nop),
        }
        return single, pair

    def test_direct_native_cli_starts_without_repo_pythonpath(self):
        root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable,
             str(root / "tools/check_baldosa_wide_overlap_causality.py"),
             "--help"],
            env=env, cwd=root, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--front-slot", result.stdout)

    def test_equal_rgb_redundancy_is_causal_union_not_owner(self):
        s, f, r, nof, nop = self.d
        q = classify(s, f, r, nof, nop, frame=1856, first_slot=98)
        self.assertEqual(q["status"], "observed")
        self.assertEqual(q["pixel_counts"]["source_union"], 3)
        self.assertEqual(q["pixel_counts"]["source_overlap"], 1)
        self.assertEqual(q["pixel_counts"]["redundant_pair_colour_causality"], 1)
        self.assertEqual(q["pixel_counts"]["changed_without_front"], 1)
        self.assertEqual(q["pixel_counts"]["changed_without_pair"], 3)
        self.assertEqual(q["bounded_xy_examples"]["redundant_pair_colour"],
                         [[101, 40]])
        self.assertFalse(q["winner_identity_proven"])
        self.assertFalse(q["release_hd_admission"])
        result = verify_native(s, f, r, nof, nop, *self.reports(),
                               frame=1856, first_slot=98)
        self.assertTrue(result["native_single_and_pair_reports_verified"])

    def test_three_interventions_identify_redundant_colour_without_winner(self):
        stock, front, rear, no_front, no_pair = self.d
        no_rear = bytearray(stock)
        # Rear-only source at (102,40) drives output. The front-only
        # source at 100 is unchanged; at equal-colour overlap 101 either
        # deletion alone has no RGB effect, but deleting both does.
        pix(no_rear, 102, 40, 9, 10, 11, 0)
        no_rear = bytes(no_rear)
        single, pair = self.reports()
        report = {
            "status": "observed-rear-color-change",
            "guest_frame": 1856, "rear_slot": 99,
            "guest_crc_equal_in_all_three_processes": True,
            "native_rear_remove_exactly_armed": True,
            "stock_sha256": hashlib.sha256(stock).hexdigest(),
            "rear_source_sha256": hashlib.sha256(rear).hexdigest(),
            "removed_sha256": hashlib.sha256(no_rear).hexdigest(),
            "rear_deletion_changed_pixels": 1,
            "rear_deletion_changed_outside_source": 0,
            "rear_source_emitted_pixels": 2,
        }
        result = correlate_authenticated_rear(
            stock, front, rear, no_front, no_rear, no_pair,
            single, pair, report, frame=1856, first_slot=98,
        )
        c = result["authenticated_three_interventions"]["pixel_counts"]
        self.assertEqual(c["front_removal_changes"], 1)
        self.assertEqual(c["rear_removal_changes"], 1)
        self.assertEqual(c["paired_removal_changes"], 3)
        self.assertEqual(c["neither_single_changes_but_pair_does"], 1)
        self.assertEqual(c["overlap_equal_rgb_pair_only_causality"], 1)
        self.assertEqual(c["front_only_causal_signature"], 1)
        self.assertEqual(c["rear_only_causal_signature"], 1)
        self.assertEqual(c["triple_nonlocal_source_violation"], 0)
        self.assertEqual(
            result["authenticated_three_interventions"]["bounded_xy_examples"]
            ["pair_only_equal_rgb"], [[101, 40]])
        self.assertFalse(
            result["authenticated_three_interventions"]
            ["unique_original_ppu_winner_proven"])
        self.assertFalse(
            result["authenticated_three_interventions"]["release_hd_admission"])
        forged = {**report, "removed_sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "provenance"):
            correlate_authenticated_rear(
                stock, front, rear, no_front, no_rear, no_pair,
                single, pair, forged, frame=1856, first_slot=98)
        forged = {**report, "rear_deletion_changed_pixels": 0}
        with self.assertRaisesRegex(ValueError, "disagrees"):
            correlate_authenticated_rear(
                stock, front, rear, no_front, no_rear, no_pair,
                single, pair, forged, frame=1856, first_slot=98)

    def test_rear_only_zero_delta_still_authenticates_without_hd_admission(self):
        stock, front, rear, no_front, no_pair = self.d
        single, pair = self.reports()
        report = {
            "status": "observed-no-rear-color-change",
            "guest_frame": 1856, "rear_slot": 99,
            "guest_crc_equal_in_all_three_processes": True,
            "native_rear_remove_exactly_armed": True,
            "stock_sha256": hashlib.sha256(stock).hexdigest(),
            "rear_source_sha256": hashlib.sha256(rear).hexdigest(),
            "removed_sha256": hashlib.sha256(stock).hexdigest(),
            "rear_deletion_changed_pixels": 0,
            "rear_deletion_changed_outside_source": 0,
            "rear_source_emitted_pixels": 2,
        }
        found = correlate_authenticated_rear(
            stock, front, rear, no_front, stock, no_pair,
            single, pair, report, frame=1856, first_slot=98)
        observed = found["authenticated_three_interventions"]
        self.assertEqual(observed["pixel_counts"]["rear_removal_changes"], 0)
        self.assertFalse(observed["unique_original_ppu_winner_proven"])
        self.assertFalse(observed["release_hd_admission"])

    def test_unknown_owner_or_native_provenance_is_never_accepted(self):
        s, f, r, nof, nop = self.d
        single, pair = self.reports()
        pair["counterfactual_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "paired-PPU provenance"):
            verify_native(s, f, r, nof, nop, single, pair,
                          frame=1856, first_slot=98)
        pair["counterfactual_sha256"] = hashlib.sha256(nop).hexdigest()
        single["native_ppu_final_contributed_pixels"] = 2
        with self.assertRaisesRegex(ValueError, "counters"):
            verify_native(s, f, r, nof, nop, single, pair,
                          frame=1856, first_slot=98)
        with self.assertRaisesRegex(ValueError, "contiguous"):
            classify(s, f, r, nof, nop, frame=1856, first_slot=99)
        with self.assertRaisesRegex(ValueError, "342x224"):
            classify(s[:-4], f, r, nof, nop, frame=1856, first_slot=98)

    def test_foreign_colour_change_blocks_causality(self):
        s, f, r, nof, nop = self.d
        mutated = bytearray(nop)
        pix(mutated, 300, 210, 250, 12, 13, 0)
        report = classify(s, f, r, nof, mutated,
                          frame=1856, first_slot=98)
        self.assertEqual(report["status"], "unproven")
        self.assertEqual(report["pixel_counts"]["pair_changed_outside_union"], 1)


if __name__ == "__main__":
    unittest.main()
