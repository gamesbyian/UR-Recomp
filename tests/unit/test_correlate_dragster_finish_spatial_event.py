from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import correlate_dragster_finish_spatial_event as mod


class DragsterFinishSpatialTriangulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(mod.SPATIAL.read_text(encoding="utf-8"))

    def test_retained_dynamic_event_matches_finish_column_exactly(self):
        report = mod.correlate(self.contract, dict(mod.DEFAULT_EVENT))
        self.assertEqual(report["matched_packed_word"], "2020")
        self.assertEqual(report["matched_c000_slot"], 8)
        self.assertEqual(report["matching_cell_count"], 6)
        self.assertEqual(report["nearest_finish_x_cell_count"], 3)
        self.assertEqual(report["closest_historical_finish_x_distance"], 2)
        self.assertEqual(report["player_to_nearest_cell_x_distance"], 24)
        self.assertEqual(
            sorted(c["world_rect"] for c in report["nearest_finish_x_cells"]),
            [
                [25280, 800, 25295, 815],
                [25280, 832, 25295, 847],
                [25280, 864, 25295, 879],
            ],
        )
        self.assertIn("Without verified contact Y", report["limits"])
        self.assertEqual(
            report["observation_phase"], "postframe_stored_p1_contact"
        )
        self.assertIn(
            "not necessarily the word consumed by same-frame object dispatch",
            report["observation_limit"],
        )
        rendered = mod.markdown(report)
        self.assertIn("postframe surface sample", rendered)
        self.assertIn("postframe_stored_p1_contact", rendered)
        self.assertIn("dispatch precedes new contact sampling", rendered)

    def test_word_to_slot_is_independent_of_upper_control_bits(self):
        self.assertEqual(mod.surface_slot(0x2020), 8)
        self.assertEqual(mod.surface_slot(0x2820), 8)
        self.assertIsNone(mod.surface_slot(0x4000))

    def test_mismatched_event_fails_closed(self):
        event = dict(mod.DEFAULT_EVENT)
        event["object_index"] = 9
        with self.assertRaisesRegex(ValueError, "does not decode"):
            mod.correlate(self.contract, event)
        event = dict(mod.DEFAULT_EVENT)
        event["object_code"] = 0x12
        with self.assertRaisesRegex(ValueError, "not a checkpoint/finish-family"):
            mod.correlate(self.contract, event)
        event = dict(mod.DEFAULT_EVENT)
        event["player_x"] = 65536
        with self.assertRaisesRegex(ValueError, "outside course world extent"):
            mod.correlate(self.contract, event)
        event = dict(mod.DEFAULT_EVENT)
        event["collision_word"] = 0x1020
        with self.assertRaisesRegex(ValueError, "no ROM-derived course cell"):
            mod.correlate(self.contract, event)

    def test_can_consume_original_object_activation_analyzer_schema(self):
        row = {
            "frame": 2903, "player_x": 25256, "player_y": 835,
            "collision_word": 0x2020, "object_index": 8,
            "object_code": 0x14,
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "activation.json"
            path.write_text(
                json.dumps({"first_progress_change": row}), encoding="utf-8"
            )
            event = mod.event_from_activation_json(path)
        self.assertEqual(event["player_y"], 835)
        self.assertEqual(event["object_index"], 8)
        self.assertEqual(event["observation_phase"], "postframe_stored_p1_contact")
        self.assertEqual(mod.correlate(self.contract, event)["nearest_finish_x_cell_count"], 3)

    def test_missing_original_event_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "activation.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no first_progress_change"):
                mod.event_from_activation_json(path)


if __name__ == "__main__":
    unittest.main()
