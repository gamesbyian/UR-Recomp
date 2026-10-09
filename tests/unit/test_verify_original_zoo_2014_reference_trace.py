"""Original 2014 Snes9x raw write-trace reproducibility contracts."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_original_zoo_2014_reference_trace as tool


def change(f: int, addr: int, before: int, after: int) -> bytes:
    return (json.dumps({
        "f": f, "adr": f"0x{addr:05x}",
        "old": f"0x{before:02x}", "val": f"0x{after:02x}",
    }, separators=(",", ":")) + "\n").encode("utf-8")


class OriginalZooRawTraceReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.witness = json.loads(tool.WITNESS.read_text(encoding="utf-8"))

    def test_raw_trace_grouping_preserves_postframe_values_and_write_order(self):
        lines = [
            change(1, 0x0313, 0, 1),
            change(1, 0x00CE, 0, 1),
            change(1, 0x1199, 0, 0),
            change(2, 0x0EF1, 0, 4),
            change(2, 0x0411, 0, 0xF0),
            change(2, 0x0412, 0, 0x23),
            change(3, 0x0EF1, 4, 3),
            change(3, 0x1199, 0, 1),
            change(3, 0x119D, 0, 1),
            change(4, 0x0415, 0, 1),
        ]
        result = tool.reconstruct(lines, frozenset((1, 2, 3, 4)))
        self.assertEqual(result["raw_record_count"], len(lines))
        self.assertEqual(result["last_written_frame"], 4)
        self.assertEqual(result["trace_sha256"],
                         hashlib.sha256(b"".join(lines)).hexdigest())
        self.assertEqual(result["samples"][2]["p1_world_xy"], [9200, 0])
        self.assertEqual(result["samples"][2]["progress"], [0, 0, 4])
        self.assertEqual(result["samples"][3]["progress"], [1, 1, 3])
        self.assertEqual(result["samples"][4]["p1_world_xy"], [9200, 1])
        self.assertEqual(result["direct_progress_writes"][3], [
            {"wram_offset_hex": "0EF1", "old": 4, "new": 3},
            {"wram_offset_hex": "1199", "old": 0, "new": 1},
            {"wram_offset_hex": "119D", "old": 0, "new": 1},
        ])
        self.assertIsNone(tool.surface_slot(0))
        self.assertEqual(tool.surface_slot(0x2304), 194)
        self.assertEqual(tool.surface_slot(0x0F20), 200)

    def test_monotonicity_and_missing_expected_frame_fail(self):
        source = [change(2, 0x1199, 0, 1), change(1, 0x1199, 1, 2)]
        with self.assertRaisesRegex(tool.TraceWitnessError, "monotonic"):
            tool.reconstruct(source, frozenset((1, 2)))
        with self.assertRaisesRegex(tool.TraceWitnessError, "frame.*missing"):
            tool.reconstruct([change(1, 0x1199, 0, 1)], frozenset((2,)))

    def test_reduced_source_recheck_fail_closed_on_bytes_and_event_values(self):
        w = self.witness
        initial = w["initial_active_frame"]
        samples = {
            3190: {
                "movie_frame": 3190,
                "menu": initial["menu"], "in_race": initial["in_race"],
                "track_id": initial["track_id"],
                "p1_world_xy": initial["p1_world_xy"],
                "p2_world_xy": initial["p2_world_xy"],
                "progress": [initial[x] for x in (
                    "p1_next_checkpoint", "p1_finish_gate", "p1_laps_remaining"
                )],
                "timer_raw_digits": initial["timer_raw_digits"],
            }
        }
        onset = w["original_race_start_phase"]
        samples[3394] = {
            "movie_frame": 3394,
            "p1_world_xy": [9200, 1563],
            "timer_raw_digits": [0, 0, 0, 0, 0],
        }
        samples[3395] = {
            "movie_frame": 3395,
            "p1_world_xy": [onset["first_p1_moving_x"], 1562],
            "p1_speed_x": onset["first_p1_signed_vx"],
            "p1_boost": onset["first_p1_boost_nonzero"],
            "timer_raw_digits": onset["stopwatch_at_first_motion"],
        }
        samples[3396] = {
            "movie_frame": 3396,
            "timer_raw_digits": onset["stopwatch_at_first_timer_tick"],
        }
        writes = {}
        within_frame = {}
        for row in w["observed_progression"]:
            frame = row["transition_frame"]
            for index, (at, key) in enumerate((
                (frame-1, "progress_before"),
                (frame, "progress_after"),
            )):
                xy_key = "p1_world_xy_before" if index == 0 else "p1_world_xy_after"
                word_key = ("p1_stored_contact_before_hex" if index == 0 else
                            "p1_stored_contact_after_hex")
                raw_progress = row[key]
                samples[at] = {
                    "movie_frame": at,
                    "p1_world_xy": row[xy_key],
                    "p1_stored_contact_word": int(row[word_key], 16),
                    "progress": [raw_progress[k] for k in (
                        "checkpoint", "finish_gate", "laps_remaining"
                    )],
                    "timer_raw_digits": row["original_timer_raw_digits"],
                }
            writes[frame] = row["observed_original_progress_writes"]
            within_frame[frame] = row["original_lowwram_write_sequence"]
        result = {
            "trace_sha256": w["provenance"]["source_sha256"],
            "raw_record_count": w["provenance"]["raw_trace_write_records"],
            "last_written_frame": w["observed_original_up_to_frame"],
            "samples": samples,
            "direct_progress_writes": writes,
            "within_frame_event_write_sequence": within_frame,
        }
        qualified = tool.verify(result, w)
        self.assertTrue(qualified["qualified_original_write_trace"])
        self.assertEqual(qualified["original_event_frames_reproduced"],
                         [3408, 3794, 4031, 4722, 4911])
        self.assertEqual(qualified["lap_counter_decrements"], [3408, 4911])
        self.assertEqual(qualified["original_first_horizontal_x_change_frame"], 3395)
        self.assertEqual(qualified["original_first_stopwatch_tick_frame"], 3396)
        for event in w["observed_progression"]:
            sequence = event["original_lowwram_write_sequence"]
            self.assertEqual(sequence, sorted(sequence, key=lambda x: x["zero_based_write_index_in_frame"]))
        for event in (w["observed_progression"][0], w["observed_progression"][-1]):
            sequence = event["original_lowwram_write_sequence"]
            self.assertEqual(sequence[0]["wram_offset_hex"], "0E95")
            self.assertIn("0EF1", [x["wram_offset_hex"] for x in sequence[1:]])
        changed = copy.deepcopy(result)
        changed["trace_sha256"] = "0" * 64
        with self.assertRaisesRegex(tool.TraceWitnessError, "source hash"):
            tool.verify(changed, w)
        changed = copy.deepcopy(result)
        changed["samples"][3794]["progress"][0] = 42
        with self.assertRaisesRegex(tool.TraceWitnessError, "checkpoint"):
            tool.verify(changed, w)
        changed = copy.deepcopy(result)
        changed["direct_progress_writes"][4911].reverse()
        with self.assertRaisesRegex(tool.TraceWitnessError, "write order"):
            tool.verify(changed, w)
        changed = copy.deepcopy(result)
        changed["within_frame_event_write_sequence"][3408].reverse()
        with self.assertRaisesRegex(tool.TraceWitnessError, "within-frame write order"):
            tool.verify(changed, w)


if __name__ == "__main__":
    unittest.main()
