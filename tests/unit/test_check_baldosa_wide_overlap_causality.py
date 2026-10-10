"""Causal overlap diagnostics never infer a unique painter from identical RGB."""
import hashlib
import unittest

from tools.check_baldosa_wide_overlap_causality import (
    classify, verify_native,
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
