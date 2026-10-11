"""Adversarial exact Original/OBJ source tests for countdown foreground."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_2p_countdown_source_occlusion import (
    assess, COUNTDOWN_RGB, FRAMES, SLOTS, EXISTING_CAPTURED_FRAMES,
    WIDTH, HEIGHT,
)
from tools.check_baldosa_wide_single_slot_source import HEADER, read_source


class Original2PCountdownCoverTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("baldosa-evidence", "baldosa-ws342-captures",
                     "baldosa-ws342-obj-slots"):
            (self.root / name).mkdir()
        self.original = {}
        self.source = {}
        for frame in FRAMES:
            original = bytearray(bytes((110, 110, 110, 255)) * WIDTH * HEIGHT)
            self.source[frame] = {}
            if frame in (1872, 1888):
                # Stationary blue foreground rectangle covers *moving*
                # lower OBJ alpha positions. Its mask must be exactly
                # equal across these two distinct native-style frames.
                for y in range(155, 161):
                    for x in range(80, 122):
                        at = (y * WIDTH + x) * 4
                        original[at:at + 4] = bytes((*COUNTDOWN_RGB, 255))
            for slot in SLOTS:
                plane = bytearray(WIDTH * HEIGHT * 4)
                x = 70 + 8 * (slot & 1) + (frame - 1856)
                y = 45 if slot >= 98 else 158
                at = 4 * (y * WIDTH + x)
                rgba = bytes((slot, 44, 22, 255))
                plane[at:at + 4] = rgba
                if slot == 98 or (frame == 1856 and slot == 96):
                    original[at:at + 4] = rgba
                elif slot < 98 and frame != 1856:
                    original[at:at + 4] = bytes((*COUNTDOWN_RGB, 255))
                self.source[frame][slot] = plane
            self.original[frame] = original
        self.flush()

    def source_path(self, frame, slot):
        return (self.root / "baldosa-ws342-obj-slots" /
                f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam")

    def report_path(self, frame, slot):
        suffix = f"_frame{frame}" if frame != 1856 else ""
        return self.root / "baldosa-evidence" / f"ws342_obj_slot_{slot}{suffix}.json"

    def stock_path(self, frame):
        return (self.root / "baldosa-ws342-captures" /
                f"ur-baldosa-ws342-{frame:06d}.pam")

    def flush(self):
        for frame in FRAMES:
            original = bytes(self.original[frame])
            self.stock_path(frame).write_bytes(HEADER + original)
            sha = hashlib.sha256(original).hexdigest()
            for slot in SLOTS:
                path = self.source_path(frame, slot)
                path.write_bytes(HEADER + self.source[frame][slot])
                meta = read_source(path, slot)
                self.report_path(frame, slot).write_text(json.dumps({
                    "schema_version": 1,
                    "status": "passed",
                    "source_log_matches_pam": True,
                    "identical_complete_original_342_rasters": 6,
                    "differing_original_rasters": [],
                    "shared_full_frame_guest_ids": EXISTING_CAPTURED_FRAMES,
                    "minimum_shared_frames": 4,
                    "source": meta,
                    "source_frame_main_raster_sha256": sha,
                    "guest_crc_comparison":
                        "Externally enforced byte-exact in native workflow",
                }), encoding="utf-8")

    def test_positive_lower_cover_with_valid_upper_and_pre_overlay_controls(self):
        witness = assess(self.root)
        self.assertEqual(witness["independently_verified_source_exports"], 12)
        self.assertEqual(witness["countdown_2_uniform_rgb"], [57, 57, 255])
        for frame in (1872, 1888):
            row = witness["per_original_frame"][str(frame)]
            lower = row["source_union_by_raster_band"]["lower"]
            self.assertTrue(lower["all_source_coordinates_final_blue"])
            for slot in (96, 97):
                self.assertEqual(row["per_slot"][str(slot)]
                                 ["source_rgb_matches_final_original"], 0)
            self.assertEqual(row["per_slot"]["98"]
                             ["source_rgb_matches_final_original"], 1)
        self.assertFalse(witness["per_original_frame"]["1856"]
                         ["source_union_by_raster_band"]["lower"]
                         ["all_source_coordinates_final_blue"])
        self.assertFalse(witness["safe_to_promote_hd_racer_rendering"])
        self.assertFalse(witness["foreground_numeral_source_layer_proven"])
        self.assertTrue(witness["countdown_2_blue_final_mask_temporally_equal_1872_1888"])
        self.assertTrue(witness["source_slot_rgb_and_alpha_changed_while_blue_mask_constant"])
        self.assertEqual(
            witness["per_original_frame"]["1872"]["full_original_blue_rgb_mask_sha256"],
            witness["per_original_frame"]["1888"]["full_original_blue_rgb_mask_sha256"])

    def test_single_blue_byte_difference_changes_witness(self):
        plane = self.source[1872][96]
        at = (plane.index(255) // 4) * 4
        self.original[1872][at + 2] = 254
        self.flush()
        with self.assertRaisesRegex(
                ValueError, "blue overlay mask changed|countdown-covering witness"):
            assess(self.root)

    def test_countdown_blue_mask_drift_outside_racers_fails_closed(self):
        # The source alpha can remain fully covered while unrelated blue
        # countdown pixels shift. Compare the WHOLE native Original colour
        # mask, not just pixels under original emitted OAM slots.
        pos = (155 * WIDTH + 120) * 4
        self.original[1888][pos:pos + 4] = bytes((110, 110, 110, 255))
        self.flush()
        with self.assertRaisesRegex(ValueError, "blue overlay mask changed"):
            assess(self.root)

    def test_static_lower_alpha_behind_blue_mask_fails_motion_claim(self):
        # Preserve the stationary blue rectangle; instead duplicate an
        # older lower rider source so the supposed motion witness is false.
        self.source[1888][96] = bytearray(self.source[1872][96])
        self.flush()
        with self.assertRaisesRegex(ValueError, "alpha is static"):
            assess(self.root)

    def test_stale_or_forged_source_digest_rejected(self):
        plane = self.source[1888][97]
        at = (plane.index(255) // 4) * 4
        plane[at + 1] ^= 1
        self.source_path(1888, 97).write_bytes(HEADER + plane)
        with self.assertRaisesRegex(ValueError, "provenance invalid"):
            assess(self.root)

    def test_stale_original_raster_rejected_despite_self_consistent_reports(self):
        self.original[1888] = bytearray(self.original[1872])
        self.flush()
        with self.assertRaisesRegex(ValueError, "not three distinct"):
            assess(self.root)

    def test_source_in_wrong_original_split_band_rejected(self):
        plane = self.source[1856][96]
        at = (plane.index(255) // 4) * 4
        plane[at:at + 4] = bytes(4)
        plane[4 * (15 * WIDTH + 70):4 * (15 * WIDTH + 70) + 4] = (
            bytes((96, 44, 22, 255)))
        self.flush()
        with self.assertRaisesRegex(ValueError, "lower split source alpha leaked"):
            assess(self.root)

    def test_report_source_identity_and_full_stock_sha_guard(self):
        file = self.report_path(1872, 98)
        report = json.loads(file.read_text())
        report["source_frame_main_raster_sha256"] = "0" * 64
        file.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "provenance invalid"):
            assess(self.root)

    def test_missing_original_2p_frame_rejected(self):
        self.stock_path(1888).unlink()
        with self.assertRaises(FileNotFoundError):
            assess(self.root)


if __name__ == "__main__":
    unittest.main()
