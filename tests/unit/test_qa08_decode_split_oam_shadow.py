"""Synthetic only; no native PPU acceptance or invented racer pixels."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.qa08_decode_split_oam_shadow import audit, inspect_bytes


class SplitOamShadowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = bytearray(0x20000)
        self.data[0x0DDB:0x0DDD] = bytes([1, 0])
        self.data[0x121B:0x121D] = bytes([0, 0])
        self.data[0x121D:0x121F] = bytes([0, 0])
        self.data[0x1501:0x1511] = bytes([
            0xFF, 0xF0, 0x12, 0x40,  # slot96
            0x10, 0x50, 0x13, 0x41,  # slot97
            0x20, 0x60, 0x14, 0x42,  # slot98
            0x30, 0x70, 0x15, 0x43,  # slot99
        ])
        self.data[0x1599] = 0xA5

    def write(self, tag, data=None):
        (self.root / f"{tag}.wram.bin").write_bytes(data or self.data)

    def test_a5_and_5a_describe_four_independent_two_bit_fields(self):
        row = inspect_bytes(bytes(self.data))
        self.assertEqual([s["x_msb"] for s in row["oam_high_slots96_99"]],
                         [1, 1, 0, 0])
        self.assertEqual([s["size_select"] for s in row["oam_high_slots96_99"]],
                         [0, 0, 1, 1])
        self.assertEqual([s["slot"] for s in row["reserved_slots"]],
                         [96, 97, 98, 99])
        self.assertEqual(row["reserved_slots"][0]["x_unsigned9"], 511)
        self.assertEqual(row["reserved_slots"][0]["x_signed9_wrapped"], -1)
        self.assertEqual(row["reserved_slots"][0]["y_unsigned8"], 0xF0)
        self.assertEqual(row["reserved_slots"][0]["possible_sentinel_or_offscreen"],
                         "unclassified")
        self.assertEqual(row["second_camera_enable_0ddb_raw_word"], 1)
        self.assertEqual(row["offscreen_flags_121b_121d_raw_words"], [0, 0])
        self.data[0x1599] = 0x5A
        row = inspect_bytes(bytes(self.data))
        self.assertEqual([s["x_msb"] for s in row["oam_high_slots96_99"]],
                         [0, 0, 1, 1])
        self.assertEqual(row["reserved_slots"][2]["x_unsigned9"], 0x120)

    def test_synthetic_0x70_low_x_flips_between_split_bands(self):
        # Structural bit arithmetic only; this isn't a real raster capture.
        for slot in range(4):
            self.data[0x1501 + 4 * slot] = 0x70
        self.data[0x1599] = 0xA5
        upper = inspect_bytes(bytes(self.data))
        self.data[0x1599] = 0x5A
        lower = inspect_bytes(bytes(self.data))
        self.assertEqual(
            [s["x_unsigned9"] for s in upper["reserved_slots"]],
            [0x170, 0x170, 0x070, 0x070],
        )
        self.assertEqual(
            [s["x_unsigned9"] for s in lower["reserved_slots"]],
            [0x070, 0x070, 0x170, 0x170],
        )
        self.assertEqual(
            [s["x_signed9_wrapped"] for s in upper["reserved_slots"]],
            [-144, -144, 112, 112],
        )

    def test_repeated_unchanged_offscreen_flags_do_not_mask_oam_changes(self):
        self.write("endurance-1740")
        self.data[0x1599] = 0x5A
        self.data[0x1509] = 0x90
        self.write("endurance-2580")
        out = audit(self.root, ["endurance-1740", "endurance-2580"])
        change = out["transitions"][0]
        self.assertTrue(change["high_shadow_byte_changed"])
        self.assertEqual(change["changed_reserved_oam_shadow_slots"],
                         [96, 97, 98, 99])
        self.assertFalse(change["second_camera_raw_changed"])
        self.assertFalse(out["actual_active_display_high_oam_captured"])
        self.assertFalse(out["source_obj_emission_or_final_raster_verified"])
        self.assertFalse(out["remastered_racer_admission"])
        self.assertEqual(out["checkpoints"][0]["offscreen_flags_121b_121d_raw_words"],
                         [0, 0])
        self.assertEqual(len(out["checkpoints"][0]["wram_sha256"]), 64)

    def test_only_one_low_oam_slot_change_detected(self):
        self.write("a")
        self.data[0x150E] ^= 1
        self.write("b")
        change = audit(self.root, ["a", "b"])["transitions"][0]
        self.assertEqual(change["changed_reserved_oam_shadow_slots"], [99])
        self.assertFalse(change["high_shadow_byte_changed"])

    def test_bad_size_or_missing_or_duplicate_snapshot_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "exact 128 KiB"):
            inspect_bytes(bytes(0x1FFFF))
        with self.assertRaises(FileNotFoundError):
            audit(self.root, ["not-captured"])
        self.write("a")
        with self.assertRaisesRegex(ValueError, "distinct"):
            audit(self.root, ["a", "a"])
        with self.assertRaisesRegex(ValueError, "invalid checkpoint"):
            audit(self.root, ["../escape"])
        with self.assertRaisesRegex(ValueError, "nonempty"):
            audit(self.root, [])

    def test_high_shadow_is_not_a_boolean_or_final_ppu_observer(self):
        self.data[0x1599] = 0
        row = inspect_bytes(bytes(self.data))
        self.assertEqual(row["oam_high_shadow_1599"], 0)
        self.assertEqual(len(row["oam_high_slots96_99"]), 4)
        self.assertNotIn("visible", row["reserved_slots"][0])
        self.assertNotIn("raster", row["reserved_slots"][0])


if __name__ == "__main__":
    unittest.main()
