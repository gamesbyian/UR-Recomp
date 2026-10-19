"""ROM-free adversarial QA08 grayscale spatial localization tests."""
import sys
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_localize_112field_grayscale as spatial


def images(pairs):
    original = bytearray(spatial.WIDTH * spatial.HEIGHT * 4)
    native = bytearray(len(spatial.source.P7_HEADER) + len(original))
    native[:len(spatial.source.P7_HEADER)] = spatial.source.P7_HEADER
    for x, y, ref, got in pairs:
        pos = (y * spatial.WIDTH + x) * 4
        original[pos:pos+4] = bytes((ref[2] << 3, ref[1] << 3, ref[0] << 3, 0))
        pos += len(spatial.source.P7_HEADER)
        native[pos:pos+4] = bytes((got[0] << 3, got[1] << 3, got[2] << 3, 0))
    return bytes(original), bytes(native)


class AuthenticRasterSpatialTests(unittest.TestCase):
    def test_full_rgb5_partition_and_edge_pixels(self):
        original, native = images([
            (0, 0, (15,15,15), (20,20,20)),
            (7, 8, (6,6,6), (5,5,5)),
            (8, 8, (14,7,9), (14,7,8)),
            (255, 223, (1,2,3), (1,2,3)),
            (255, 112, (20,20,20), (17,17,17)),
        ])
        result = spatial.classify_frame(original, native)
        self.assertEqual(len(result), 256*224)
        self.assertEqual(result[0], spatial.CYCLE)
        self.assertEqual(result[8*256+7], spatial.OTHER_GRAY)
        self.assertEqual(result[8*256+8], spatial.CHROMATIC)
        self.assertEqual(result[112*256+255], spatial.CYCLE)
        self.assertEqual(result[223*256+255], spatial.EXACT)
        self.assertEqual(result.count(spatial.CYCLE), 2)
        self.assertEqual(result.count(spatial.OTHER_GRAY), 1)
        self.assertEqual(result.count(spatial.CHROMATIC), 1)
        self.assertEqual(result.count(spatial.EXACT), 256*224-4)

    def test_bad_source_shape_header_and_fourth_channel_refused(self):
        original, native = images([])
        with self.assertRaisesRegex(ValueError, "raster shape"):
            spatial.classify_frame(original[:-4], native)
        with self.assertRaisesRegex(ValueError, "raster shape"):
            spatial.classify_frame(original, native[:-4])
        with self.assertRaisesRegex(ValueError, "raster shape"):
            spatial.classify_frame(original, b"bogus" + native[5:])
        bad = bytearray(native)
        bad[len(spatial.source.P7_HEADER)+3] = 255
        with self.assertRaisesRegex(ValueError, "fourth channel"):
            spatial.classify_frame(original, bytes(bad))
        bad = bytearray(original)
        bad[3] = 255
        with self.assertRaisesRegex(ValueError, "fourth channel"):
            spatial.classify_frame(bytes(bad), native)

    def test_13_real_guest_labels_temporal_overlap_and_conservation(self):
        frames = [bytearray(spatial.WIDTH*spatial.HEIGHT)
                  for _ in spatial.source.SPIKES]
        for i, frame in enumerate(frames):
            frame[0] = spatial.CYCLE
            frame[8] = spatial.CYCLE if i % 2 else spatial.OTHER_GRAY
            frame[spatial.WIDTH * 112 + 255] = spatial.CHROMATIC
        result = spatial.summarize_classes(frames)
        counts = result["class_counts"]
        self.assertEqual(counts["four_cycle"], 19)
        self.assertEqual(counts["other_grayscale_wrong"], 7)
        self.assertEqual(counts["non_grayscale_wrong"], 13)
        self.assertEqual(result["cycle_position_union"], 2)
        self.assertEqual(result["cycle_position_intersection_all_13"], 1)
        self.assertEqual(result["scanline_counts"]["four_cycle"][0], 19)
        self.assertEqual(result["scanline_counts"]["non_grayscale_wrong"][112], 13)
        self.assertEqual(result["tile_8x8_counts"]["four_cycle"][0], 13)
        self.assertEqual(result["tile_8x8_counts"]["four_cycle"][1], 6)
        self.assertEqual(result["tile_8x8_counts"]["non_grayscale_wrong"][14*32+31], 13)
        self.assertEqual(result["frames"][0]["original_callback"], 4063)
        self.assertEqual(result["frames"][-1]["native_guest"], 5408)
        for key in ("original_native_consumed_inputs_and_beam_equivalent",
                    "CGRAM_ingestion_or_register_root_cause_proven",
                    "global_frame_shift_palette_recolour_or_brightness_patch_authorized",
                    "QA08_QA10_or_release_accepted"):
            self.assertIs(result[key], False)

    def test_truncated_duplicate_and_impossible_class_refused(self):
        clean = [bytearray(spatial.WIDTH*spatial.HEIGHT)
                 for _ in spatial.source.SPIKES]
        with self.assertRaisesRegex(ValueError, "exactly 13"):
            spatial.summarize_classes(clean[:-1])
        with self.assertRaisesRegex(ValueError, "exactly 13"):
            spatial.summarize_classes(clean + [clean[0]])
        clean[0][0] = 42
        with self.assertRaisesRegex(ValueError, "invalid RGB5"):
            spatial.summarize_classes(clean)

    def test_committed_real_source_receipt_conserves_all_counts_and_hold(self):
        path = ROOT / "analysis/data/qa08-authentic-grayscale-spatial-20261019.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["original_inner_sha256"], spatial.source.ORIGINAL_INNER_SHA)
        self.assertEqual(receipt["native_outer_sha256"], spatial.source.NATIVE_OUTER_SHA)
        self.assertEqual(receipt["native_guest_5484_crc_sha256"], spatial.source.NATIVE_CRC_SHA)
        self.assertEqual(receipt["frame_labels"], list(spatial.source.SPIKES))
        classes = receipt["class_counts"]
        self.assertEqual(classes["four_cycle_gray_to_gray_wrong"], 318775)
        self.assertEqual(classes["other_gray_to_gray_wrong"], 23311)
        self.assertEqual(classes["non_grayscale_wrong"], 16927)
        self.assertEqual(classes["all_RGB5_wrong"], 359013)
        self.assertEqual(sum(classes[k] for k in (
            "exact_RGB5", "four_cycle_gray_to_gray_wrong",
            "other_gray_to_gray_wrong", "non_grayscale_wrong")),
            13 * spatial.WIDTH * spatial.HEIGHT)
        self.assertEqual([x["guest"] for x in receipt["per_frame"]],
                         list(spatial.source.SPIKES))
        self.assertEqual([sum(row[k] for row in receipt["per_frame"])
                          for k in ("cycle", "other_gray", "non_gray")],
                         [318775, 23311, 16927])
        self.assertEqual(receipt["four_cycle_pixel_position_union_13_frames"], 24940)
        self.assertEqual(receipt["four_cycle_pixel_position_intersection_all_13"], 24096)
        self.assertEqual(receipt["spatial_grid"]["cycle_cells_all_64_pixels_wrong_in_every_frame"], 289)
        self.assertEqual(receipt["entire_original_native_263_frame_wrong_RGB5_baseline_unchanged"],
                         890205)
        self.assertFalse(receipt["qa08_qa10_release_gates_accepted"])
        self.assertTrue(receipt["no_source_clock_or_beam_causality_proven"])

    def test_direct_script_cli_reaches_archive_fail_closed_guard(self):
        cmd = [sys.executable, str(ROOT / "tools/qa08_localize_112field_grayscale.py"),
               "--original", str(ROOT / "missing-original-qa08.zip"),
               "--native", str(ROOT / "missing-native-qa08.zip")]
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                             check=False)
        self.assertEqual(run.returncode, 2)
        self.assertIn("QA08_GRAY_SPATIAL_REFUSED:", run.stderr)
        self.assertNotIn("ImportError", run.stderr)

    def test_provenance_verification_must_run_before_archives_open(self):
        with patch.object(spatial.source, "verify",
                          side_effect=ValueError("bad archive")):
            with self.assertRaisesRegex(ValueError, "bad archive"):
                spatial.analyze(Path("fake-original.zip"), Path("fake-native.zip"))


if __name__ == "__main__":
    unittest.main()
