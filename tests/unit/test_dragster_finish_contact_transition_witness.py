from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from correlate_dragster_finish_spatial_event import (
    SPATIAL, correlate, surface_slot,
)

WITNESS = ROOT / "analysis/data/dragster-finish-contact-transition.json"


class DragsterFinishContactTransitionWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trace = json.loads(WITNESS.read_text(encoding="utf-8"))
        cls.contract = json.loads(SPATIAL.read_text(encoding="utf-8"))

    def test_guest_native_witness_is_bounded_and_provenanced(self):
        self.assertEqual(self.trace["provenance"]["workflow_run"], 36954104693)
        self.assertEqual(self.trace["provenance"]["workflow_artifact_id"], 11204794758)
        self.assertIn("not an independent emulator", self.trace["provenance"]["authority"])
        rows = self.trace["samples"]
        self.assertEqual([r["relative_frame"] for r in rows], list(range(172, 179)))
        self.assertEqual([r["frame"] for r in rows], list(range(2901, 2908)))
        self.assertEqual({r["player_y"] for r in rows}, {857})

    def test_contact_selector_matches_runtime_c000_slot_for_every_frame(self):
        for row in self.trace["samples"]:
            self.assertEqual(
                surface_slot(row["collision_word"]), row["object_index"],
                row["relative_frame"],
            )

    def test_progression_occurs_between_two_0x14_behavior_selections(self):
        rows = self.trace["samples"]
        old, event, after = rows[1], rows[2], rows[3]
        self.assertEqual(old["relative_frame"], 173)
        self.assertEqual(event["relative_frame"], 174)
        self.assertEqual(old["object_code"], 0x14)
        self.assertEqual(event["object_code"], 0x14)
        self.assertEqual(old["object_index"], 10)
        self.assertEqual(event["object_index"], 8)
        self.assertEqual(old["collision_word"], 0x2024)
        self.assertEqual(event["collision_word"], 0x2020)
        self.assertEqual(
            (old["checkpoint"], old["finish_gate"], old["laps_remaining"]),
            (3, 0, 1),
        )
        self.assertEqual(
            (event["checkpoint"], event["finish_gate"], event["laps_remaining"]),
            (1, 1, 0),
        )
        self.assertEqual(
            (after["checkpoint"], after["finish_gate"], after["laps_remaining"]),
            (1, 1, 0),
        )

    def test_all_confirmed_checkpoint_family_contacts_have_exact_rom_cells(self):
        by_slot = {}
        for row in self.trace["samples"]:
            if row["object_code"] != 0x14:
                continue
            event = dict(row, source=self.trace["provenance"]["artifact_member"])
            result = correlate(self.contract, event)
            self.assertEqual(result["matched_c000_slot"], row["object_index"])
            self.assertGreater(result["matching_cell_count"], 0)
            by_slot[row["object_index"]] = result

        self.assertEqual(set(by_slot), {8, 9, 10})
        self.assertEqual(by_slot[8]["player_center_y"], 857)
        self.assertEqual(by_slot[8]["nearest_player_center_y_gap_at_finish_x"], 7)
        self.assertEqual(
            [p["world_rect"] for p in by_slot[8]["nearest_center_y_cells_at_finish_x"]],
            [[25280, 864, 25295, 879]],
        )

        self.assertEqual(
            {p["world_rect"][0] for p in by_slot[8]["nearest_finish_x_cells"]},
            {25280},
        )
        self.assertEqual(
            {p["world_rect"][0] for p in by_slot[10]["nearest_finish_x_cells"]},
            {25280},
        )
        self.assertEqual(
            {p["world_rect"][0] for p in by_slot[9]["nearest_finish_x_cells"]},
            {25296},
        )
        self.assertEqual(
            sorted(p["world_rect"][1] for p in by_slot[8]["nearest_finish_x_cells"]),
            [800, 832, 864],
        )
        self.assertEqual(
            sorted(p["world_rect"][1] for p in by_slot[10]["nearest_finish_x_cells"]),
            [816, 848, 880],
        )
        self.assertEqual(
            sorted(p["world_rect"][1] for p in by_slot[9]["nearest_finish_x_cells"]),
            [800, 832, 864],
        )


if __name__ == "__main__":
    unittest.main()
