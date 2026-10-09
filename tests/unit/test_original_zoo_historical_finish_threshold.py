"""Original Snes9x Zoom Zoo counters a naive historical finish-X threshold.

The archival TAS optimizer's hard-coded finish X is not a guest completion
contract. Two *actual original Snes9x* active-circuit snapshots are on
opposite sides of that number without either being an end result. This
test pins only that limited refutation, not real 16x16 contact causality.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANDMARKS = ROOT / "analysis/generated/dessyreqt-course-landmarks.json"
ARCHIVED = ROOT / "analysis/generated/historical-2014-first-race-replay.json"


class OriginalZooFinishXCounterexampleTests(unittest.TestCase):
    def test_original_active_race_straddles_optimizer_finish_x(self):
        raw = json.loads(LANDMARKS.read_text(encoding="utf-8"))
        zoo = next(row for row in raw["tracks"] if row["track_id"] == 1)
        self.assertEqual(zoo["name"], "Zoom Zoo")
        self.assertEqual(zoo["finish_x"], 8881)
        evidence = json.loads(ARCHIVED.read_text(encoding="utf-8"))
        self.assertEqual(evidence["source_movie"],
                         "reference/imported/tas-bots/dessyreqt-4250-submission.smv")
        by_frame = {entry["frame"]: entry
                    for entry in evidence["sampled_mismatches"]}
        # Tuple fields: menu, inRace, track, P1_x, P1_y, P1_vx,
        # P1_vy, airtime, pitch. These are ORIGINAL reference columns;
        # prior native absolute-frame samples are not scene-synchronized.
        before = by_frame[3400]["reference"]
        after = by_frame[3800]["reference"]
        self.assertEqual(before[:3], [0, 1, 1])
        self.assertEqual(after[:3], [0, 1, 1])
        self.assertEqual(before[3], 9098)
        self.assertEqual(after[3], 8565)
        self.assertGreater(before[3], zoo["finish_x"])
        self.assertLess(after[3], zoo["finish_x"])
        # Both are active Zoo guest states, so a position-only comparison
        # against the historical constant is not an accepted finish rule.
        self.assertNotEqual(before[0], 0x99)
        self.assertNotEqual(after[0], 0x99)

    def test_original_above_threshold_is_not_a_terminal_result(self):
        evidence = json.loads(ARCHIVED.read_text(encoding="utf-8"))
        for frame in (3400, 4200, 4600):
            row = next(x["reference"] for x in evidence["sampled_mismatches"]
                       if x["frame"] == frame)
            with self.subTest(frame=frame):
                self.assertEqual(row[:3], [0, 1, 1])
                self.assertGreater(row[3], 8881)


if __name__ == "__main__":
    unittest.main()
