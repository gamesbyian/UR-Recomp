"""ROM-free tests: original 2014 SMV scene-relative sample extraction."""
from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract_historical_smv_scene_window as mod


def synthetic_movie(raw_samples: list[int]) -> tuple[bytes, dict]:
    save_off, controller_off = 128, 160
    data = bytearray(controller_off + 2 * len(raw_samples))
    data[:4] = b"SMV\x1a"
    struct.pack_into("<I", data, 4, 4)
    struct.pack_into("<I", data, 8, 0x12345678)
    struct.pack_into("<I", data, 0x20, len(raw_samples))
    data[0x14] = 1
    data[0x15] = 1
    data[0x17] = 0x40
    struct.pack_into("<I", data, 0x18, save_off)
    struct.pack_into("<I", data, 0x1C, controller_off)
    struct.pack_into("<I", data, save_off - 30 + 3, 0x383858C7)
    for i, mask in enumerate(raw_samples):
        struct.pack_into("<H", data, controller_off + i * 2, mask)
    return bytes(data), {
        "version": 4,
        "uid": 0x12345678,
        "sample_count": len(raw_samples),
        "controller_mask": 1,
        "controller_data_offset": controller_off,
        "reset_anchored": True,
        "rom_info": {"crc32": "383858c7"},
    }


class SceneInputWindowTests(unittest.TestCase):
    def test_bounded_scene_relative_run_mapping(self):
        source, meta = synthetic_movie([0x8000, 0x8000, 0, 0x0100, 0x0110, 0x0110])
        report = mod.window(source, meta, 0, 6)
        self.assertEqual(report["movie_frame_range"], [0, 5])
        self.assertEqual(
            report["relative_input_segments"],
            [
                {"start": 0, "duration": 2, "mask": "0x001"},
                {"start": 3, "duration": 1, "mask": "0x080"},
                {"start": 4, "duration": 2, "mask": "0x880"},
            ],
        )
        self.assertIn("NOT a known race entry", report["source_limit"])
        shifted = mod.shifted_input_file(report, 1000)
        rows = [x for x in shifted.splitlines() if not x.startswith("#")]
        self.assertEqual(rows, ["1000:2:001", "1003:1:080", "1004:2:880"])
        self.assertIn("caller-supplied", shifted)

    def test_subrange_can_be_rebased_without_changing_event_lengths(self):
        source, meta = synthetic_movie([0x8000, 0x8000, 0, 0x0100, 0x0110, 0x0110])
        report = mod.window(source, meta, 2, 4)
        self.assertEqual(report["movie_frame_range"], [2, 5])
        self.assertEqual(report["relative_input_segments"], [
            {"start": 1, "duration": 1, "mask": "0x080"},
            {"start": 2, "duration": 2, "mask": "0x880"},
        ])

    def test_malformed_anchor_and_original_movie_identity_fail_closed(self):
        source, meta = synthetic_movie([0, 1, 2])
        for change in ({"uid": 123}, {"sample_count": 10}, {"version": 1},
                       {"controller_mask": 2}, {"reset_anchored": False},
                       {"rom_info": {"crc32": "00000000"}},
                       {"controller_data_offset": 999}):
            with self.subTest(change=change):
                with self.assertRaises(mod.MovieWindowError):
                    mod.window(source, dict(meta, **change), 0, 3)
        for first, frames in ((-1, 1), (0, 0), (0, mod.LIMIT + 1), (2, 2)):
            with self.assertRaises(mod.MovieWindowError):
                mod.window(source, meta, first, frames)
        with self.assertRaises(mod.MovieWindowError):
            mod.window(source[:70], meta, 0, 3)

    def test_reset_markers_and_reserved_bits_are_not_silent_input(self):
        for word in (0xFFFF, 0x8001):
            data, meta = synthetic_movie([0x8000, word])
            with self.assertRaisesRegex(mod.MovieWindowError, "reset marker or reserved"):
                mod.window(data, meta, 0, 2)

    def test_zip_wrapper_exactly_one_smv(self):
        data, _ = synthetic_movie([0, 0x8000])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw.smv"
            raw.write_bytes(data)
            self.assertEqual(mod.read_movie(raw), (data, None))
            single = root / "one.zip"
            with zipfile.ZipFile(single, "w") as zf:
                zf.writestr("nested/movie.smv", data)
            self.assertEqual(mod.read_movie(single), (data, "nested/movie.smv"))
            double = root / "two.zip"
            with zipfile.ZipFile(double, "w") as zf:
                zf.writestr("one.smv", data)
                zf.writestr("two.smv", data)
            with self.assertRaisesRegex(mod.MovieWindowError, "exactly one"):
                mod.read_movie(double)

    def test_unverified_guest_alignment_must_be_explicit(self):
        source, meta = synthetic_movie([0x8000])
        report = mod.window(source, meta, 0, 1)
        for bad in (-1, None, 1.5, True):
            with self.assertRaises(mod.MovieWindowError):
                mod.shifted_input_file(report, bad)


if __name__ == "__main__":
    unittest.main()
