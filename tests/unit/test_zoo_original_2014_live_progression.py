"""Original 2014 Snes9x Zoom Zoo course-progress oracle, not native parity."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract_historical_smv_scene_window as smv
from correlate_dragster_finish_spatial_event import surface_slot
from probe_course_checkpoint_placements import (
    ROM, USA_SHA256, c000_resource_ranges,
)
from analyze_course_resource_lists import parse_course_resource_list
from analyze_rnc_streams import find_streams
from rnc_method1 import unpack_method1

WITNESS = ROOT / "analysis/data/zoo-original-2014-live-progression.json"
CATALOG = ROOT / "analysis/data/course-corpus.json"
TRANSITION_FRAMES = [3408, 3794, 4031, 4722, 4911]
EXPECTED_BEFORE = [(0, 0, 4), (1, 1, 3), (2, 1, 3), (3, 0, 3), (0, 0, 3)]
EXPECTED_AFTER = [(1, 1, 3), (2, 1, 3), (3, 0, 3), (0, 0, 3), (1, 1, 2)]


class ZooOriginal2014LiveProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.witness = json.loads(WITNESS.read_text(encoding="utf-8"))
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.events = cls.witness["observed_progression"]

    def test_exact_original_source_and_independent_status(self):
        w = self.witness
        self.assertEqual(w["schema_version"], 1)
        p = w["provenance"]
        self.assertEqual(p["workflow_run_id"], 37184022134)
        self.assertEqual(p["artifact_id"], 11296685866)
        self.assertEqual(p["raw_trace_write_records"], 669690)
        self.assertEqual(
            p["source_sha256"],
            "5fc0e88c89d2dc35b945a2c1f37f522fe8ba3090ea64a0efe50e1748b39f93ab",
        )
        self.assertEqual(p["rom_sha256"], USA_SHA256)
        self.assertEqual(w["course"], {
            "id": "course:02", "name": "Zoom Zoo",
            "event_kind": "circuit-a", "track_id": 1,
        })
        self.assertFalse(w["native_parity_compared"])
        self.assertFalse(w["circuit_result_reached"])
        self.assertEqual(w["observed_original_up_to_frame"], 5000)

    def test_first_original_live_racer_positions_calibrate_header_not_optimizer(self):
        row = self.witness["initial_active_frame"]
        course = self.catalog["courses"][1]
        self.assertEqual((row["movie_frame"], row["track_id"], row["in_race"]),
                         (3190, 1, 1))
        self.assertEqual(row["p1_world_xy"], [9200, 1489])
        self.assertEqual(row["p2_world_xy"], [9200, 1489])
        self.assertEqual(row["header_A_world_xy"], [9200, 1488])
        self.assertEqual(row["header_B_world_xy"], [9200, 1488])
        for pair_name in ("a", "b"):
            self.assertEqual(
                [value * 16 for value in course["header"][f"spawn_or_landmark_{pair_name}"]],
                row[f"header_{pair_name.upper()}_world_xy"],
            )
        self.assertEqual(course["historical_landmarks"]["start_x"],
                         row["historical_unused_optimizer_start_x"])
        self.assertNotEqual(row["historical_unused_optimizer_start_x"],
                            row["p1_world_xy"][0])
        self.assertEqual([row[x] for x in (
            "p1_next_checkpoint", "p1_finish_gate", "p1_laps_remaining"
        )], [0, 0, 4])

    def test_five_original_progression_events_preserve_order_and_direct_writes(self):
        self.assertEqual([r["transition_frame"] for r in self.events],
                         TRANSITION_FRAMES)
        self.assertEqual([
            tuple(r["progress_before"][k] for k in (
                "checkpoint", "finish_gate", "laps_remaining"))
            for r in self.events
        ], EXPECTED_BEFORE)
        self.assertEqual([
            tuple(r["progress_after"][k] for k in (
                "checkpoint", "finish_gate", "laps_remaining"))
            for r in self.events
        ], EXPECTED_AFTER)
        direct_address_map = {
            "checkpoint": 0x1199, "finish_gate": 0x119D,
            "laps_remaining": 0x0EF1,
        }
        for record in self.events:
            self.assertEqual(record["prior_postframe"], record["transition_frame"] - 1)
            actual = [(int(w["wram_offset_hex"], 16), w["old"], w["new"])
                      for w in record["observed_original_progress_writes"]]
            expected = {
                (address, record["progress_before"][name],
                 record["progress_after"][name])
                for name, address in direct_address_map.items()
                if record["progress_before"][name] != record["progress_after"][name]
            }
            self.assertEqual(set(actual), expected)
            self.assertEqual(len(actual), len(expected))
            self.assertEqual(
                surface_slot(int(record["p1_stored_contact_before_hex"], 16)),
                record["prior_contact_c000_slot_candidate"],
            )
            self.assertEqual(
                surface_slot(int(record["p1_stored_contact_after_hex"], 16)),
                record["new_postframe_contact_slot"],
            )
        self.assertEqual(
            [row["original_timer_raw_digits"] for row in self.events],
            [[0, 0, 0, 2, 1], [0, 0, 6, 6, 3],
             [0, 1, 0, 6, 0], [0, 2, 2, 1, 1],
             [0, 2, 5, 2, 4]],
        )
        self.assertEqual(self.witness["initial_active_frame"]["timer_raw_digits"],
                         [0, 0, 0, 0, 0])
        self.assertEqual(self.events[-1]["p1_world_xy_after"], [8961, 1568])
        self.assertEqual(
            self.events[-1]["transition_frame"] - self.events[0]["transition_frame"],
            1503,
        )
        self.assertEqual([
            r["transition_frame"] for r in self.events
            if r["progress_before"]["laps_remaining"]
            != r["progress_after"]["laps_remaining"]
        ], [3408, 4911])

    def test_checkpoint_wrap_is_not_a_lap_decrement_in_the_original_game(self):
        events = {row["transition_frame"]: row for row in self.events}
        rearm = events[4031]
        wrap = events[4722]
        lap = events[4911]
        self.assertEqual(rearm["progress_before"],
                         {"checkpoint": 2, "finish_gate": 1, "laps_remaining": 3})
        self.assertEqual(rearm["progress_after"],
                         {"checkpoint": 3, "finish_gate": 0, "laps_remaining": 3})
        self.assertEqual(wrap["progress_before"],
                         {"checkpoint": 3, "finish_gate": 0, "laps_remaining": 3})
        self.assertEqual(wrap["progress_after"],
                         {"checkpoint": 0, "finish_gate": 0, "laps_remaining": 3})
        self.assertEqual(lap["progress_before"],
                         {"checkpoint": 0, "finish_gate": 0, "laps_remaining": 3})
        self.assertEqual(lap["progress_after"],
                         {"checkpoint": 1, "finish_gate": 1, "laps_remaining": 2})
        self.assertEqual(lap["transition_frame"] - wrap["transition_frame"], 189)
        # Never model checkpoint 3->0 as a lap award. It is 189 original
        # guest frames before the next observed lap decrement.

    def test_exact_original_movie_input_masks_at_each_event(self):
        movie, member = smv.read_movie(smv.ARCHIVE)
        self.assertEqual(member, "100% run.smv")
        metadata = json.loads(smv.METADATA.read_text(encoding="utf-8"))
        trace = smv.window(movie, metadata, 3190, 1810)
        runs = trace["relative_input_segments"]
        for row in self.events:
            relative = row["transition_frame"] - 3190
            found = [
                int(run["mask"], 16)
                for run in runs
                if run["start"] <= relative < run["start"] + run["duration"]
            ]
            self.assertEqual(
                found, [int(row["controller_mask_at_transition"], 16)],
                f"original movie mask mismatched event {row['transition_frame']}"
            )

    def test_original_contact_candidates_are_in_rom_checkpoint_family(self):
        if not ROM.is_file():
            self.skipTest("private canonical USA cartridge absent")
        rom = ROM.read_bytes()
        import hashlib
        self.assertEqual(hashlib.sha256(rom).hexdigest(), USA_SHA256)
        stream = list(find_streams(rom))[1]
        parsed = parse_course_resource_list(unpack_method1(stream[1]))
        spans = [
            (r["start"], r["end"])
            for r in c000_resource_ranges(rom, parsed["resource_ids"])
            if r["resource_id"] == 0x24
        ]
        self.assertTrue(spans)
        for e in self.events:
            for field in ("prior_contact_c000_slot_candidate", "new_postframe_contact_slot"):
                slot = e[field]
                self.assertTrue(
                    any(start <= slot <= end for start, end in spans),
                    f"frame {e['transition_frame']} {field} slot {slot}"
                )


if __name__ == "__main__":
    unittest.main()
