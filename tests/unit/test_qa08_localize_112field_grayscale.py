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

    def test_real_cgram_word_permutation_matches_gray_class_types_only(self):
        packet_path = ROOT / "analysis/data/qa08-late-cgram-four-color-raster-crossjoin-20261019.json"
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        seen = {}
        for row in packet["palette_packets_by_CGRAM_index"]:
            old = int(row["original_5178_RGB555"], 16)
            new = int(row["native_5183_RGB555"], 16)
            def gray_level(word):
                channels = ((word >> 0) & 31, (word >> 5) & 31, (word >> 10) & 31)
                self.assertEqual(len(set(channels)), 1)
                self.assertGreater(channels[0], 0)
                return channels[0] - 1  # candidate quantization only
            ref, native = gray_level(old), gray_level(new)
            self.assertEqual((ref, native),
                             (row["implied_original_gray_RGB5"],
                              row["implied_native_gray_RGB5"]))
            self.assertIn((ref, native), spatial.source.CYCLE)
            seen[f"{ref}->{native}"] = row["genuine_observed_pixel_occurrences_13_frames"]
        self.assertEqual(seen, {"15->20":53658, "16->15":107868,
                                "17->16":52716, "20->17":104533})
        self.assertEqual(sum(seen.values()), 318775)
        self.assertIs(packet["four_of_four_observed_pair_types_match_packet_permutation"], True)
        for boundary in ("actual_original_native_effective_PPU_CGRAM_at_render_proven",
                         "pixel_to_palette_index_source_consumption_proven",
                         "original_native_guest_instruction_clock_and_H_counter_equivalence_proven",
                         "same_native_PE_between_register_and_raster_archives",
                         "source_color_to_RGB5_minus_one_is_mechanistically_proven",
                         "palette_recolor_frame_shift_brightness_or_CPU_timing_change_authorized",
                         "QA08_QA10_or_release_gate_accepted"):
            self.assertIs(packet[boundary], False)

    def test_late_seven_field_bracket_classification_and_bad_controls(self):
        frames = [bytearray(spatial.WIDTH*spatial.HEIGHT)
                  for _ in spatial.source.SPIKES]
        for frame in frames:
            frame[0] = spatial.CYCLE
            frame[1] = spatial.CYCLE
        controls = {f:bytearray(spatial.WIDTH*spatial.HEIGHT)
                    for f in spatial.LATE_BRACKET}
        controls[5184][0] = spatial.CYCLE
        controls[5184][1] = spatial.CYCLE
        report = spatial.classify_late_writer_bracket(frames, controls)
        self.assertEqual(report["persistent_source_positions"], 2)
        self.assertEqual([x["native_guest"] for x in report["correctly_registered_seven_fields"]],
                         list(spatial.LATE_BRACKET))
        self.assertEqual([x["four_cycle_wrong_RGB5"]
                          for x in report["correctly_registered_seven_fields"]],
                         [0, 0, 0, 2, 0, 0, 0])
        self.assertTrue(all(x["original_callback"] == x["native_guest"]-1
                            for x in report["correctly_registered_seven_fields"]))
        self.assertIs(report["PPU_CGRAM_or_beam_causality_proven"], False)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            spatial.classify_late_writer_bracket(
                frames, {k:v for k,v in controls.items() if k != 5184})
        frames[0] = bytearray(spatial.WIDTH*spatial.HEIGHT-1)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            spatial.classify_late_writer_bracket(frames, controls)

    def test_committed_sevenfield_control_receipt_is_source_bound_and_releaseless(self):
        path = ROOT / "analysis/data/qa08-authentic-sevenfield-gray-pulse-bracket-20261019.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["original_callback_inner_zip_sha256"], spatial.source.ORIGINAL_INNER_SHA)
        self.assertEqual(data["native_Win32_integrated_outer_zip_sha256"], spatial.source.NATIVE_OUTER_SHA)
        self.assertEqual(data["real_native_guest_CRC_sha256"], spatial.source.NATIVE_CRC_SHA)
        self.assertEqual(data["persistent_cycle_position_count"], 24096)
        self.assertEqual(data["persistent_cycle_position_index_uint32le_sha256"],
                         "4646f2123c596b1e9bbca6813d92b1ae3b9a4a53e08e300c17bf2e5f2ebb7b95")
        rows = data["seven_frames"]
        self.assertEqual([r["native_guest"] for r in rows], list(spatial.LATE_BRACKET))
        self.assertEqual([r["stable_positions_RGB5_exact"] for r in rows],
                         [24096,24096,24096,0,24096,24096,24096])
        self.assertEqual([r["stable_positions_RGB5_gray_cycle_wrong"] for r in rows],
                         [0,0,0,24096,0,0,0])
        self.assertTrue(all(r["original_callback"] == r["native_guest"]-1 for r in rows))
        self.assertTrue(all(len(r["original_BGRX_sha256"]) == 64 and
                            len(r["native_P7_sha256"]) == 64 for r in rows))
        self.assertFalse(data["QA08_QA10_or_release_accepted"])
        self.assertFalse(data["per_pixel_consumed_CGRAM_slot_and_color_math_proven"])

    def test_per_coordinate_fixed_gray_class_never_changes_silently(self):
        original, native = images([
            (0, 0, (15,15,15), (20,20,20)),
            (8, 112, (16,16,16), (15,15,15)),
            (8, 16, (1,2,3), (1,2,4)),
        ])
        pixels = spatial.classify_cycle_pair_map(original, native)
        self.assertEqual(pixels[0], 1)
        self.assertEqual(pixels[112*spatial.WIDTH+8], 2)
        self.assertEqual(pixels[16*spatial.WIDTH+8], 0)
        frames = [bytearray(spatial.WIDTH*spatial.HEIGHT)
                  for _ in spatial.source.SPIKES]
        for i, f in enumerate(frames):
            f[0] = 1
            if i % 2 == 0:
                f[112*spatial.WIDTH+8] = 2
        result = spatial.summarize_cycle_pair_identity(frames)
        self.assertEqual(result["union_positions"], 2)
        self.assertEqual(result["intersection_positions_all_13"], 1)
        self.assertEqual(result["cross_class_coordinate_conflicts"], 0)
        self.assertEqual([r["intersection_source_positions_all_13"]
                          for r in result["per_gray_pair"]], [1,0,0,0])
        self.assertEqual([r["sampled_pixel_occurrences"]
                          for r in result["per_gray_pair"]], [13,7,0,0])
        self.assertEqual(result["per_gray_pair"][1]["lower_raster_intersection_source_positions"], 0)
        self.assertFalse(result["CGRAM_effective_pixel_index_proven"])
        frames[4][0] = 3
        with self.assertRaisesRegex(ValueError, "changed its gray-cycle class"):
            spatial.summarize_cycle_pair_identity(frames)
        frames[4][0] = 1
        frames[4][1] = 5
        with self.assertRaisesRegex(ValueError, "unknown cycle-class"):
            spatial.summarize_cycle_pair_identity(frames)
        with self.assertRaisesRegex(ValueError, "exactly 13"):
            spatial.summarize_cycle_pair_identity(frames[:-1])

    def test_authenticated_four_class_spatial_receipt_retains_negative_causality(self):
        path = ROOT / "analysis/data/qa08-authentic-fixed-gray-class-20261019.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["original_2014_inner_sha256"], spatial.source.ORIGINAL_INNER_SHA)
        self.assertEqual(receipt["native_integrated_outer_sha256"], spatial.source.NATIVE_OUTER_SHA)
        self.assertEqual(receipt["native_guest_CRC_sha256"], spatial.source.NATIVE_CRC_SHA)
        rows = receipt["actual_pair_class_spatial_identity"]["per_gray_pair"]
        self.assertEqual([x["original_to_native_RGB5"] for x in rows],
                         ["15->20", "16->15", "17->16", "20->17"])
        self.assertEqual([x["union_source_positions"] for x in rows],
                         [4181,8380,4131,8248])
        self.assertEqual([x["intersection_source_positions_all_13"] for x in rows],
                         [4088,8236,3969,7803])
        self.assertEqual([x["sampled_pixel_occurrences"] for x in rows],
                         [53658,107868,52716,104533])
        classes = receipt["actual_pair_class_spatial_identity"]
        self.assertEqual(classes["cross_class_coordinate_conflicts"],0)
        self.assertEqual(classes["union_positions"],24940)
        self.assertEqual(classes["intersection_positions_all_13"],24096)
        self.assertEqual(classes["all_frame_observed_cycle_pixels"],318775)
        self.assertFalse(classes["CGRAM_effective_pixel_index_proven"])
        self.assertFalse(classes["release_QA08_QA10_accepted"])

    def test_original_full_cgram_readback_vs_native_input_receipt(self):
        receipt = json.loads((ROOT / "analysis/data/qa08-original-full-cgram-stable-vs-native-port-20261019.json").read_text())
        self.assertEqual(receipt["original_zip_sha256"],
                         "d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8")
        self.assertEqual(receipt["native_current_RF017_zip_sha256"],
                         "a62f0c228e85c741a8f1da0b92a4444f9091681c065c93c8a678b4ee2bb6f2ef")
        self.assertEqual(receipt["native_compiled_guest_CRC_sha256"], spatial.source.NATIVE_CRC_SHA)
        self.assertEqual(receipt["original_both_snapshots_bytes"], 512)
        self.assertTrue(receipt["original_both_full_CGRAM_snapshots_identical"])
        self.assertEqual(receipt["original_both_snapshots_sha256"],
                         "431224685084e4a1ec62da7d7aaab96a7c36beb78aa8d257b0569be416737c12")
        self.assertEqual(receipt["original_previous_source_frame"], 5183)
        self.assertEqual(receipt["original_next_source_frame"], 5184)
        self.assertEqual(receipt["original_last_observed_four_word_writer_frame"], 5178)
        old = [int(x,16) for x in receipt["original_effective_full_CGRAM_words_6c_to_6f"]]
        new = [int(x,16) for x in receipt["native_CPU_submitted_words_6c_to_6f"]]
        self.assertEqual(old, [0x56b5, 0x4a52, 0x4631, 0x4210])
        self.assertEqual(new, [old[1], old[2], old[3], old[0]])
        self.assertTrue(all(a != b for a,b in zip(old,new)))
        packets = json.loads((ROOT / "analysis/data/qa08-late-cgram-four-color-raster-crossjoin-20261019.json").read_text())["palette_packets_by_CGRAM_index"]
        self.assertEqual([int(row["original_5178_RGB555"],16) for row in packets],old)
        self.assertEqual([int(row["native_5183_RGB555"],16) for row in packets],new)
        self.assertFalse(receipt["native_effective_PPU_CGRAM_words_at_render_proven"])
        self.assertFalse(receipt["native_actual_pixel_palette_indices_proven"])
        self.assertFalse(receipt["same_original_native_CPU_instruction_and_beam_phase_proven"])
        self.assertFalse(receipt["QA08_QA10_release_acceptance"])
        self.assertTrue(receipt["no_palette_recolour_frame_shift_CPU_clock_or_renderer_fix_authorized"])

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
