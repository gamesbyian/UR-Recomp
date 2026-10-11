"""Original native 2P OAM 98↔97 and 99↔96 RGBA alias regression."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_2p_split_obj_rgba_symmetry import (
    assess, FRAMES, SLOTS, VERTICAL_DELTA, SOURCE_FRAMES,
)
from tools.check_baldosa_wide_single_slot_source import (
    WIDTH, HEIGHT, HEADER, read_source,
)


class OriginalSplitObjAliasTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "baldosa-ws342-obj-slots").mkdir()
        (self.root / "baldosa-evidence").mkdir()
        self.source = {}
        # A and B are distinct palettes and geometry, but each is
        # *exactly* copied across two hardware OAM slots and Y+113.
        for frame in FRAMES:
            self.source[frame] = {}
            for slot in SLOTS:
                pix = bytearray(WIDTH * HEIGHT * 4)
                group = "a" if slot in (97, 98) else "b"
                top = slot in (98, 99)
                x = 71 if group == "a" else 113
                y = (43 if top else 43 + VERTICAL_DELTA) + (
                    FRAMES.index(frame))
                self.put(pix, x, y, (50, 30, 230, 255) if group == "a"
                         else (210, 60, 20, 255))
                self.put(pix, x + 1, y, (120, 120, 120, 255))
                self.put(pix, x, y + 1, (8, 8, 8, 255))
                self.source[frame][slot] = pix
        self.flush_all()

    @staticmethod
    def put(data, x, y, pixel):
        offset = (y * WIDTH + x) * 4
        data[offset:offset + 4] = bytes(pixel)

    def source_file(self, slot, frame):
        return (self.root / "baldosa-ws342-obj-slots" /
                f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam")

    def report_file(self, slot, frame):
        name = (f"ws342_obj_slot_{slot}.json" if frame == FRAMES[0]
                else f"ws342_obj_slot_{slot}_frame{frame}.json")
        return self.root / "baldosa-evidence" / name

    def flush(self, slot, frame):
        f = self.source_file(slot, frame)
        f.write_bytes(HEADER + self.source[frame][slot])
        meta = read_source(f, slot)
        digest = hashlib.sha256(f"synthetic-main-{frame}".encode()).hexdigest()
        self.report_file(slot, frame).write_text(json.dumps({
            "schema_version": 1,
            "status": "passed",
            "source_log_matches_pam": True,
            "identical_complete_original_342_rasters": 6,
            "differing_original_rasters": [],
            "shared_full_frame_guest_ids": list(SOURCE_FRAMES),
            "minimum_shared_frames": 4,
            "guest_crc_comparison": "Externally enforced byte-exact in native workflow",
            "source": meta,
            "source_frame_main_raster_sha256": digest,
        }), encoding="utf-8")

    def flush_all(self):
        for frame in FRAMES:
            for slot in SLOTS:
                self.flush(slot, frame)

    def test_six_verified_full_rgba_pair_translations_across_three_frames(self):
        result = assess(self.root)
        self.assertEqual(result["status"], "original-2p-six-exact-rgba-slot-aliases")
        self.assertEqual(result["original_guest_frames"], [1856, 1872, 1888])
        self.assertEqual(result["validated_independent_original_source_exports"], 12)
        self.assertEqual(result["exact_split_duplicate_pairs"], 6)
        self.assertEqual(result["translation_y_pixels"], 113)
        for frame in FRAMES:
            pairs = result["frame_observations"][str(frame)]["pairs"]
            self.assertEqual([(x["top_slot"], x["bottom_slot"]) for x in pairs],
                             [(98, 97), (99, 96)])
            self.assertEqual([x["source_opaque_rgba_pixels_in_each_view"]
                              for x in pairs], [3, 3])
            self.assertTrue(all(x["byte_exact_all_four_rgba_channels"] for x in pairs))
            self.assertTrue(all(not x["source_final_ppu_owner_proven"] for x in pairs))
        self.assertFalse(result["release_or_remastered_admission"])

    def test_one_channel_wrong_in_lower_rider_breaks_the_pair(self):
        pos = ((43 + VERTICAL_DELTA) * WIDTH + 71) * 4
        self.source[FRAMES[0]][97][pos + 1] ^= 1
        self.flush(97, FRAMES[0])
        with self.assertRaisesRegex(ValueError, "not exact RGBA"):
            assess(self.root)

    def test_one_missing_opaque_pixel_breaks_split(self):
        pos = ((43 + VERTICAL_DELTA) * WIDTH + 71) * 4 + 3
        self.source[FRAMES[0]][97][pos] = 0
        self.flush(97, FRAMES[0])
        with self.assertRaisesRegex(ValueError, "not exact RGBA"):
            assess(self.root)

    def test_swapped_source_report_original_hash_and_identity_rejected(self):
        src = self.report_file(98, 1872)
        proof = json.loads(src.read_text())
        proof["source"]["source_sha256"] = "0" * 64
        src.write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError, "validation failed"):
            assess(self.root)
        self.flush(98, 1872)
        proof = json.loads(src.read_text())
        proof["source_frame_main_raster_sha256"] = "1" * 64
        src.write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError, "disagree on frame1872"):
            assess(self.root)

    def test_incorrect_slot_source_or_unverified_full_raster_rejected(self):
        path = self.source_file(99, 1888)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            assess(self.root)
        self.flush(99, 1888)
        src = self.report_file(99, 1888)
        proof = json.loads(src.read_text())
        proof["identical_complete_original_342_rasters"] = 5
        src.write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError, "validation failed"):
            assess(self.root)


if __name__ == "__main__":
    unittest.main()
