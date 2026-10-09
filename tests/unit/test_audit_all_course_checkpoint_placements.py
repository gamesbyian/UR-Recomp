"""All-course static checkpoint placement audit, not guest finish proof."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import audit_all_course_checkpoint_placements as audit


def sample_course(index: int) -> dict:
    kind = audit.KINDS[(index - 1) % 5]
    return {
        "id": f"course:{index:02d}", "stream_index": index,
        "name": f"Synthetic course {index}",
        "track_kind": kind,
        "historical_landmarks": {"finish_x": 90},
    }


def sample_parsed(index: int) -> dict:
    kind = audit.KINDS[(index - 1) % 5]
    return {
        "resource_ids": [] if kind == "stunt" else [0x24],
        "layout_dims": [1, 4],
    }


def sample_cells() -> list[dict]:
    return [
        {
            "world_cell": [80, 0, 95, 15],
            "coarse_sector": [1, 0],
            "fine_record_id": 4,
            "local_cell": [1, 0],
            "c000_slot": 8,
        }
    ]


class AllCourseCheckpointPlacementTests(unittest.TestCase):
    def test_classification_uses_placed_cells_not_resource_presence(self):
        race = sample_course(1)
        parsed = sample_parsed(1)
        confirmed = audit.classify_course(race, parsed, sample_cells())
        self.assertTrue(confirmed["resource_0x24_listed"])
        self.assertTrue(confirmed["resource_0x24_placed"])
        self.assertEqual(confirmed["historical_finish_x_candidate_count"], 1)
        self.assertEqual(confirmed["closest_finish_x_candidate_gap"], 0)
        self.assertEqual(confirmed["priority_class"],
                         "race_finish_x_overlaps_static_candidate")

        absent = audit.classify_course(race, parsed, [])
        self.assertTrue(absent["resource_0x24_listed"])
        self.assertFalse(absent["resource_0x24_placed"])
        self.assertEqual(absent["priority_class"],
                         "race_resource_present_but_no_placed_cells")

        other_column = audit.classify_course(
            race, parsed, [dict(sample_cells()[0], world_cell=[120, 0, 135, 15])]
        )
        self.assertEqual(other_column["closest_finish_x_candidate_gap"], 30)
        self.assertEqual(other_column["priority_class"],
                         "race_finish_x_has_no_same_column_checkpoint_candidate")

    def test_all_45_denominator_and_nine_stunt_negative_cells(self):
        records = []
        for index in range(1, 46):
            course, parsed = sample_course(index), sample_parsed(index)
            cells = [] if course["track_kind"] == "stunt" else sample_cells()
            records.append(audit.classify_course(course, parsed, cells))
        report = audit.summarize(records)
        self.assertEqual(report["denominator"], 45)
        self.assertEqual(report["ordinary_race_circuit_count"], 36)
        self.assertEqual(report["timed_stunt_count"], 9)
        self.assertEqual(report["race_with_any_placed_checkpoint_family_cells"], 36)
        self.assertEqual(report["race_with_no_placed_checkpoint_family_cells"], 0)
        self.assertEqual(report["static_finish_x_nonoverlap_cases"], [])
        records[0] = audit.classify_course(sample_course(1), sample_parsed(1), [])
        changed = audit.summarize(records)
        self.assertEqual(changed["race_with_no_placed_checkpoint_family_cells"], 1)
        self.assertEqual(changed["static_finish_x_nonoverlap_cases"][0]["course_id"],
                         "course:01")
        with self.assertRaisesRegex(audit.CourseCellCensusError, "nine original"):
            audit.summarize(records[:-1])

    def test_invalid_mode_incidence_and_coordinates_rejected(self):
        stunt = sample_course(3)
        with self.assertRaisesRegex(audit.CourseCellCensusError, "mode incidence"):
            audit.classify_course(stunt, {"resource_ids": [0x24], "layout_dims": [1, 4]}, [])
        with self.assertRaisesRegex(audit.CourseCellCensusError, "without resource"):
            audit.classify_course(stunt, sample_parsed(3), sample_cells())
        bad = sample_course(1)
        bad["historical_landmarks"]["finish_x"] = 256
        with self.assertRaisesRegex(audit.CourseCellCensusError, "outside"):
            audit.classify_course(bad, sample_parsed(1), sample_cells())

    def test_canonical_usa_rom_all_45_static_course_placements(self):
        if not audit.ROM.is_file():
            self.skipTest("canonical private USA ROM not in local checkout")
        import json
        report = audit.build_report(
            audit.ROM.read_bytes(),
            json.loads(audit.CORPUS.read_text(encoding="utf-8")),
        )
        self.assertEqual(len(report["cases"]), 45)
        self.assertEqual(sum(e["resource_0x24_listed"] for e in report["cases"]), 36)
        self.assertEqual(sum(e["event_kind"] == "stunt" for e in report["cases"]), 9)
        # This is not asserted as 36/36 placements until actually measured.
        self.assertEqual(
            report["race_with_any_placed_checkpoint_family_cells"]
            + report["race_with_no_placed_checkpoint_family_cells"],
            36,
        )
        self.assertTrue(all(
            e["candidate_world_cells"] == 0
            for e in report["cases"] if e["event_kind"] == "stunt"
        ))


if __name__ == "__main__":
    unittest.main()
