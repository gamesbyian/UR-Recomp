"""ROM-backed original Zoo rider-versus-checkpoint-family geometry."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import correlate_zoo_original_positions_with_cells as probe


def cell(x0: int, y0: int, slot: int) -> dict:
    return {
        "world_cell": [x0, y0, x0 + 15, y0 + 15],
        "c000_slot": slot,
        "fine_record_id": 5,
        "coarse_sector": [x0 // 64, y0 // 64],
        "local_cell": [(x0 % 64) // 16, (y0 % 64) // 16],
    }


class ZooSourceToSpatialCellsTests(unittest.TestCase):
    def test_2d_point_distance_is_not_x_only_and_uses_inclusive_bounds(self):
        self.assertEqual(probe.point_gap(95, 95, [80, 80, 95, 95]), (0, 0))
        self.assertEqual(probe.point_gap(100, 99, [80, 80, 95, 95]), (5, 4))
        self.assertEqual(probe.point_gap(70, 60, [80, 80, 95, 95]), (10, 20))
        with self.assertRaises(probe.SpatialWitnessError):
            probe.point_gap(0, 0, [40, 40, 30, 30])
        with self.assertRaises(probe.SpatialWitnessError):
            probe.point_gap(0, 0, [10, 10, 20])

    def test_nearest_world_cell_accounts_for_both_axes(self):
        cells = [cell(80, 1000, 6), cell(112, 80, 7)]
        selected = probe.closest_cells(90, 90, cells)
        self.assertEqual(selected["nearest_c000_slot"], 7)
        self.assertEqual(selected["nearest_separate_axis_gaps"], [22, 0])
        self.assertEqual(selected["nearest_distance_squared"], 484)
        self.assertEqual(selected["inside_static_cell_count"], 0)
        selected = probe.closest_cells(83, 1005, cells)
        self.assertEqual(selected["inside_static_cell_count"], 1)
        self.assertEqual(selected["nearest_c000_slot"], 6)
        with self.assertRaisesRegex(probe.SpatialWitnessError, "no ROM-backed"):
            probe.closest_cells(0, 0, [])

    def test_rejects_forged_original_scene_and_missing_source_frame(self):
        data = json.loads(probe.REFERENCE.read_text(encoding="utf-8"))
        samples = probe.original_zoom_zoo_positions(data)
        self.assertEqual([row["movie_frame"] for row in samples], list(probe.FRAMES))
        self.assertEqual(samples[0]["x"], 9098)
        self.assertEqual(samples[0]["y"], 1568)
        self.assertEqual(samples[-1]["x"], 7587)
        changed = dict(data, source_movie="untrusted.smv")
        with self.assertRaisesRegex(probe.SpatialWitnessError, "pinned original"):
            probe.original_zoom_zoo_positions(changed)
        changed = dict(data, sampled_mismatches=[
            row for row in data["sampled_mismatches"] if row["frame"] != 3400
        ])
        with self.assertRaisesRegex(probe.SpatialWitnessError, "missing original"):
            probe.original_zoom_zoo_positions(changed)
        changed = dict(data, sampled_mismatches=[
            (dict(row, reference=[0, 0, 1, *row["reference"][3:]])
             if row["frame"] == 3400 else row)
            for row in data["sampled_mismatches"]
        ])
        with self.assertRaisesRegex(probe.SpatialWitnessError, "not an active"):
            probe.original_zoom_zoo_positions(changed)

    def test_pinned_usa_rom_original_zoo_2d_placement_witness(self):
        if not probe.ROM.is_file():
            self.skipTest("canonical private USA ROM not present locally")
        report = probe.build(
            probe.ROM.read_bytes(),
            json.loads(probe.REFERENCE.read_text(encoding="utf-8")),
        )
        self.assertEqual(report["course"], "course:02")
        self.assertEqual(report["sample_count"], 5)
        # The first actual canonical-ROM measurement is a retained,
        # source-classified witness, not a moving collision/original-vs-native
        # pass. Fail if a descriptor or coordinate transform silently drifts.
        pinned = json.loads((
            ROOT / "analysis/data/zoo-original-2014-spatial-witness.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(
            report["decoded_course_resource_0x24_candidate_cells"],
            pinned["candidate_cells"],
        )
        observed = [
            {"movie_frame": row["movie_frame"],
             "position": [row["x"], row["y"]],
             "nearest_cell": row["nearest_world_cell"],
             "axis_gap": row["nearest_separate_axis_gaps"],
             "c000_slot": row["nearest_c000_slot"],
             "inside_candidate_cells": row["inside_static_cell_count"]}
            for row in report["samples"]
        ]
        self.assertEqual(observed, pinned["samples"])
        self.assertGreater(report["decoded_course_resource_0x24_candidate_cells"], 0)
        self.assertEqual([item["movie_frame"] for item in report["samples"]],
                         list(probe.FRAMES))
        self.assertTrue(all(item["nearest_distance_squared"] >= 0
                            for item in report["samples"]))
        self.assertTrue(all(item["inside_static_cell_count"] >= 0
                            for item in report["samples"]))
        print("QA01-ZOO-ORIGINAL-2D-CELLS " + json.dumps({
            "cells": report["decoded_course_resource_0x24_candidate_cells"],
            "samples": [
                {"f": row["movie_frame"],
                 "xy": [row["x"], row["y"]],
                 "gap": row["nearest_separate_axis_gaps"],
                 "cell": row["nearest_world_cell"],
                 "slot": row["nearest_c000_slot"],
                 "inside": row["inside_static_cell_count"]}
                for row in report["samples"]
            ],
        }, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main()
