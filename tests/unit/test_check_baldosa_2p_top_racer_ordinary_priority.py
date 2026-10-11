"""Byte-strict original PPU 2P causal source partition synthetic regressions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_2p_top_racer_ordinary_priority import (
    assess, classify, verify, WIDTH, HEIGHT,
)
from tools.check_baldosa_wide_single_slot_source import HEADER, read_source


class NativeTop2PCausalSourceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("baldosa-evidence", "baldosa-ws342-captures",
                     "baldosa-ws342-obj-slots",
                     "baldosa-ws342-counterfactual-slot98",
                     "baldosa-ws342-counterfactual-slot98-frame1872"):
            (self.root / name).mkdir()
        self.scenes = {}
        for frame in (1856, 1872):
            self.scenes[frame] = self.make_scene(frame)
            self.flush(frame)

    @staticmethod
    def paint(pixels, pos, rgba):
        pixels[pos * 4:pos * 4 + 4] = bytes(rgba)

    def make_scene(self, frame):
        base = bytes((99 + (frame - 1856), 99, 99, 255))
        stock = bytearray(base * WIDTH * HEIGHT)
        without = bytearray(stock)
        front = bytearray(WIDTH * HEIGHT * 4)
        rear = bytearray(WIDTH * HEIGHT * 4)
        origin = 60 * WIDTH + 100
        positions = [origin + i for i in range(4)]
        self.paint(front, positions[0], (111, 55, 44, 255))
        self.paint(stock, positions[0], (111, 55, 44, 255))
        self.paint(without, positions[0], base)
        self.paint(front, positions[1], (211, 10, 10, 255))
        self.paint(rear, positions[1], (10, 211, 10, 255))
        self.paint(stock, positions[1], (211, 10, 10, 255))
        self.paint(without, positions[1], (10, 211, 10, 255))
        self.paint(front, positions[2], (70, 70, 70, 255))
        self.paint(rear, positions[2], (70, 70, 70, 255))
        self.paint(stock, positions[2], (70, 70, 70, 255))
        self.paint(without, positions[2], (70, 70, 70, 255))
        self.paint(rear, positions[3], (20, 200, 20, 255))
        self.paint(stock, positions[3], (20, 200, 20, 255))
        self.paint(without, positions[3], (20, 200, 20, 255))
        return {"stock": stock, "front": front, "rear": rear,
                "without": without, "positions": positions}

    def original(self, frame):
        return (self.root / "baldosa-ws342-captures" /
                f"ur-baldosa-ws342-{frame:06d}.pam")

    def removed(self, frame):
        folder = ("baldosa-ws342-counterfactual-slot98" if frame == 1856
                  else "baldosa-ws342-counterfactual-slot98-frame1872")
        return self.root / folder / f"ur-baldosa-ws342-{frame:06d}.pam"

    def source(self, frame, slot):
        return (self.root / "baldosa-ws342-obj-slots" /
                f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam")

    def source_report(self, frame, slot):
        suffix = f"_frame{frame}" if frame == 1872 else ""
        return (self.root / "baldosa-evidence" /
                f"ws342_obj_slot_{slot}{suffix}.json")

    def final_report(self, frame):
        return (self.root / "baldosa-evidence" /
                f"ws342_slot98_final_visibility_{frame}.json")

    def flush(self, frame):
        scene = self.scenes[frame]
        self.original(frame).write_bytes(HEADER + scene["stock"])
        self.removed(frame).write_bytes(HEADER + scene["without"])
        original_sha = hashlib.sha256(scene["stock"]).hexdigest()
        for slot, key in ((98, "front"), (99, "rear")):
            self.source(frame, slot).write_bytes(HEADER + scene[key])
            meta = read_source(self.source(frame, slot), slot)
            self.source_report(frame, slot).write_text(json.dumps({
                "status": "passed",
                "schema_version": 1,
                "source_log_matches_pam": True,
                "identical_complete_original_342_rasters": 6,
                "shared_full_frame_guest_ids": [1808, 1824, 1840, 1856, 1872, 1888],
                "differing_original_rasters": [],
                "source": meta,
                "source_frame_main_raster_sha256": original_sha,
            }), encoding="utf-8")
        front_sha = hashlib.sha256(scene["front"]).hexdigest()
        self.final_report(frame).write_text(json.dumps({
            "schema_version": 1, "status": "passed", "guest_frame": frame,
            "source_oam_slot": 98,
            "guest_crc_equal_in_all_three_processes": True,
            "single_slot_original_ppu_removal_armed": True,
            "source_emitted_alpha_pixels": 3,
            "native_ppu_final_contributed_pixels": 2,
            "native_ppu_changed_outside_emitted_source_alpha": 0,
            "stock_sha256": original_sha,
            "source_sha256": front_sha,
            "counterfactual_sha256":
                hashlib.sha256(scene["without"]).hexdigest(),
        }), encoding="utf-8")

    def classify(self, frame=1856):
        s = self.scenes[frame]
        return classify(bytes(s["stock"]), bytes(s["front"]),
                        bytes(s["rear"]), bytes(s["without"]))

    def test_causal_unique_overlap_equal_and_rear_only_partition(self):
        result = self.classify()
        self.assertEqual(result["status"],
                         "exact-upper-original-ppu-priority-observation")
        self.assertEqual(result["counts"]["front_only"], 1)
        self.assertEqual(result["counts"]["rear_only"], 1)
        self.assertEqual(result["counts"]["overlap_different_rgb"], 1)
        self.assertEqual(result["counts"]["overlap_equal_rgb"], 1)
        self.assertEqual(result["counts"]["front_only_removal_final_deltas"], 1)
        self.assertEqual(result["counts"]["different_overlap_final_deltas"], 1)
        self.assertEqual(result["counts"]["equal_overlap_no_final_delta"], 1)
        self.assertTrue(result["all_overlap_different_reveals_rear_rgb_on_front_removal"])
        self.assertFalse(result["source_rgb_equal_is_unique_ppu_owner_proof"])

    def test_forged_rear_reveal_fails(self):
        s = self.scenes[1856]
        self.paint(s["without"], s["positions"][1], (0, 0, 200, 255))
        self.assertEqual(self.classify()["status"], "unproven-ppu-observation")

    def test_same_rgb_overlap_cannot_claim_changed_front_owner(self):
        s = self.scenes[1856]
        self.paint(s["without"], s["positions"][2], (99, 99, 99, 255))
        self.assertGreater(self.classify()["counts"]
                           ["unexpected_original_source_priority_pixels"], 0)

    def test_changed_outside_emitted_front_fails(self):
        s = self.scenes[1856]
        self.paint(s["without"], 177 * WIDTH + 223, (1, 2, 3, 255))
        self.assertEqual(self.classify()["counts"]["other_final_changed_pixels"], 1)

    def test_real_native_source_reports_and_two_moving_frames(self):
        result = assess(self.root)
        self.assertEqual(result["status"],
                         "two-moving-native-upper-2p-front-rear-composition-witnesses")
        self.assertEqual(result["native_frames"], [1856, 1872])
        self.assertTrue(result["per_original_guest_frame"]["1872"]
                        ["source_report_and_native_deletion_verified"])
        self.assertFalse(result["safe_to_remove_original_or_author_hd"])

    def test_forged_native_removal_sha_rejected(self):
        path = self.final_report(1872)
        report = json.loads(path.read_text())
        report["counterfactual_sha256"] = "0" * 64
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "native slot98 causal report"):
            verify(self.root, 1872)

    def test_forged_source_report_main_sha_rejected(self):
        path = self.source_report(1856, 99)
        report = json.loads(path.read_text())
        report["source_frame_main_raster_sha256"] = "0" * 64
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "source slot99"):
            verify(self.root, 1856)

    def test_rear_only_not_visible_despite_valid_same_frame_reports_rejected(self):
        scene = self.scenes[1856]
        # Invented black foreground over a rear-only source has no
        # front deletion delta. Native report counts still match, but
        # an erroneous source-priority observation must be rejected.
        self.paint(scene["stock"], scene["positions"][3], (0, 0, 0, 255))
        self.paint(scene["without"], scene["positions"][3], (0, 0, 0, 255))
        self.flush(1856)
        with self.assertRaisesRegex(ValueError, "does not satisfy expected PPU"):
            verify(self.root, 1856)


if __name__ == "__main__":
    unittest.main()
