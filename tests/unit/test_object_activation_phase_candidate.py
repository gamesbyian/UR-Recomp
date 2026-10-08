"""Frame-end object-activation rows must not be promoted to handler inputs."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from analyze_object_activation_probe import prior_postframe_dispatch_candidate


def row(frame: int, word: int, slot: int, code: int) -> dict:
    return {
        "frame": frame,
        "relative_frame": frame - 2729,
        "sample": f"object-tail-{frame - 2729:03d}",
        "collision_word": word,
        "object_index": slot,
        "object_code": code,
    }


class OriginalObjectActivationPhaseContractTests(unittest.TestCase):
    def test_real_dragster_neighboring_observations_keep_both_phases(self):
        rows = [
            row(2901, 0x1804, 2, 0x12),
            row(2902, 0x2024, 10, 0x14),
            row(2903, 0x2020, 8, 0x14),
            row(2904, 0x2020, 8, 0x14),
        ]
        result = prior_postframe_dispatch_candidate(rows, rows[2])
        self.assertEqual(result["source_frame"], 2902)
        self.assertEqual(result["transition_frame"], 2903)
        self.assertEqual(result["collision_word"], 0x2024)
        self.assertEqual(result["object_index"], 10)
        self.assertEqual(result["object_code"], 0x14)
        self.assertEqual(result["status"], "candidate_only_not_instruction_time_verified")
        self.assertNotEqual(result["object_index"], rows[2]["object_index"])
        self.assertIn("intervening write", result["caveat"])

    def test_no_transition_or_missing_previous_frame_has_no_candidate(self):
        rows = [row(2902, 0x2024, 10, 0x14), row(2903, 0x2020, 8, 0x14)]
        self.assertIsNone(prior_postframe_dispatch_candidate(rows, None))
        self.assertIsNone(prior_postframe_dispatch_candidate(rows, rows[0]))
        orphan = row(2903, 0x2020, 8, 0x14)
        self.assertIsNone(prior_postframe_dispatch_candidate(rows, orphan))

    def test_gaps_and_duplicate_frame_records_fail_closed(self):
        rows = [row(2899, 0x1804, 2, 0x12), row(2903, 0x2020, 8, 0x14)]
        self.assertIsNone(prior_postframe_dispatch_candidate(rows, rows[-1]))
        rows = [row(2902, 0x2024, 10, 0x14), row(2903, 0x2020, 8, 0x14)]
        duplicate = dict(rows[-1])
        rows.append(duplicate)
        self.assertIsNone(prior_postframe_dispatch_candidate(rows, rows[1]))


if __name__ == "__main__":
    unittest.main()
