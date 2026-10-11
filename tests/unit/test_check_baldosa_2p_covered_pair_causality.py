"""Adversarial native 2P pair-removal observation under countdown RGB."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_2p_covered_pair_causality import verify, FRAME
from tools.check_baldosa_wide_single_slot_source import HEADER, WIDTH, HEIGHT, read_source


class CoveredNativePairRemovalTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.stock = root / "stock" / f"ur-baldosa-ws342-{FRAME:06d}.pam"
        self.removed = root / "removed" / f"ur-baldosa-ws342-{FRAME:06d}.pam"
        self.source = {
            s: root / "obj" / f"ur-baldosa-ws342-obj-slot{s}-frame{FRAME:06d}.pam"
            for s in (96, 97)
        }
        self.report = {s: root / "proof" / f"ws342_obj_slot_{s}_frame{FRAME}.json"
                       for s in (96, 97)}
        self.crc = {s: root / f"{s}.crc" for s in
                    ("stock", "source96", "source97", "removed")}
        self.log = root / "removed.log"
        for path in self.crc.values():
            path.write_bytes(b"00ccbbdd\n" * 5447)
        self.log.write_text(
            f"UR_RACER_HD_WIDE_REMOVE_PAIR frame={FRAME} "
            "slots=96-97 status=armed guest_unchanged=1\n", encoding="utf-8")
        self.original = bytearray(bytes((140, 140, 140, 255)) * WIDTH * HEIGHT)
        self.final = bytearray(self.original)
        self.masks = {s: bytearray(WIDTH * HEIGHT * 4) for s in (96, 97)}
        self.pixel96 = 158 * WIDTH + 110
        self.pixel97 = 158 * WIDTH + 111
        for slot, pos in ((96, self.pixel96), (97, self.pixel97)):
            self.masks[slot][4 * pos:4 * pos + 4] = bytes((slot, 25, 25, 255))
            self.original[4 * pos:4 * pos + 4] = bytes((57, 57, 255, 255))
            self.final[4 * pos:4 * pos + 4] = bytes((57, 57, 255, 255))
        self.flush()

    def flush(self):
        self.stock.parent.mkdir(parents=True, exist_ok=True)
        self.removed.parent.mkdir(parents=True, exist_ok=True)
        self.stock.write_bytes(HEADER + self.original)
        self.removed.write_bytes(HEADER + self.final)
        sha = hashlib.sha256(self.original).hexdigest()
        for slot in (96, 97):
            p = self.source[slot]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(HEADER + self.masks[slot])
            meta = read_source(p, slot)
            report = self.report[slot]
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps({
                "schema_version": 1, "status": "passed",
                "source_log_matches_pam": True,
                "identical_complete_original_342_rasters": 6,
                "differing_original_rasters": [],
                "shared_full_frame_guest_ids": [1808, 1824, 1840, 1856, 1872, 1888],
                "minimum_shared_frames": 4,
                "source": meta,
                "source_frame_main_raster_sha256": sha,
                "guest_crc_comparison": "Externally enforced byte-exact in native workflow",
            }), encoding="utf-8")

    def assess(self):
        return verify(self.stock, self.source[96], self.source[97],
                      self.removed, self.report[96], self.report[97],
                      self.crc["stock"], self.crc["source96"],
                      self.crc["source97"], self.crc["removed"], self.log)

    def test_valid_zero_final_delta_is_proven_native_negative(self):
        result = self.assess()
        self.assertEqual(result["status"], "native-covered-pair-final-unchanged")
        self.assertEqual(result["stock_vs_removed_full_final_rgba_changed_pixels"], 0)
        self.assertEqual(result["source_alpha_union_coordinates"], 2)
        self.assertEqual(result["source_coordinates_final_countdown_blue"], 2)
        self.assertEqual(result["guest_crc_equal_in_all_four_independent_native_processes"], 5447)
        self.assertFalse(result["specific_foreground_bg_obj_layer_proven"])
        self.assertFalse(result["source_slot_removal_allowed_in_product"])

    def test_valid_changed_under_source_is_observed_not_prejudged(self):
        self.final[4 * self.pixel96] = 60
        self.removed.write_bytes(HEADER + self.final)
        result = self.assess()
        self.assertEqual(result["status"], "native-covered-pair-final-changed")
        self.assertEqual(result["stock_vs_removed_full_final_rgba_changed_pixels"], 1)
        self.assertEqual(result["bounded_final_changed_xy_examples"], [[110, 158]])

    def test_changed_outside_union_rejected(self):
        outside = (170 * WIDTH + 222) * 4
        self.final[outside:outside + 4] = bytes((5, 5, 5, 255))
        self.removed.write_bytes(HEADER + self.final)
        with self.assertRaisesRegex(ValueError, "outside"):
            self.assess()

    def test_false_blue_overlay_disproves_countdown_case(self):
        self.original[self.pixel96 * 4] = 56
        self.flush()
        with self.assertRaisesRegex(ValueError, "blue countdown"):
            self.assess()

    def test_swapped_or_incomplete_guest_crc_rejected(self):
        self.crc["removed"].write_bytes(b"12345678\n" * 5447)
        with self.assertRaisesRegex(ValueError, "5447-line guest CRC"):
            self.assess()

    def test_missing_duplicate_or_wrong_slot_arm_marker_rejected(self):
        self.log.write_text("UR_RACER_HD_WIDE_REMOVE_PAIR frame=1872 slots=98-99 "
                            "status=armed guest_unchanged=1\n")
        with self.assertRaisesRegex(ValueError, "not exactly once armed"):
            self.assess()

    def test_forged_source_full_raster_sha_rejected(self):
        report = self.report[96]
        data = json.loads(report.read_text())
        data["source_frame_main_raster_sha256"] = "0" * 64
        report.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "proof incomplete"):
            self.assess()

    def test_counterfactual_cannot_alias_stock_file(self):
        self.removed = self.stock
        with self.assertRaisesRegex(ValueError, "independent native stock"):
            self.assess()


if __name__ == "__main__":
    unittest.main()
