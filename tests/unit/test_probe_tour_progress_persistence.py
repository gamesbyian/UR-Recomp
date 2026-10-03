import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_tour_progress_persistence as probe  # noqa: E402


def s(counter, in_race=0, menu=0, track=0):
    return {"menu": menu, "track": track, "in_race": in_race,
            "counters": [counter] * 3, "nonzero_medals_rows_0_7": 0}


BASELINE = {750: s(0), 1000: s(0, 1), 3000: s(1), 8500: s(2), 12000: s(3)}


def reload_run(start, after):
    return {"input_counter": start, "boot_diff": ["0x0742"],
            "samples": {300: s(start), 750: s(start), 1000: s(start, 1), 3250: s(after)}}


class TourProgressPersistenceTests(unittest.TestCase):
    def test_persisting_counter_passes(self) -> None:
        report = probe.summarize(BASELINE, {2: reload_run(2, 3), 3: reload_run(3, 4)})
        self.assertTrue(report["all_checks_pass"], report["checks"])
        self.assertEqual(report["baseline_counter_sequence"], [0, 1, 2, 3])
        self.assertEqual(report["reloads"]["2"]["counter_after_first_race"], 3)

    def test_counter_reset_on_boot_fails(self) -> None:
        run = reload_run(2, 1)
        run["samples"] = {300: s(0), 750: s(0), 1000: s(0, 1), 3250: s(1)}
        report = probe.summarize(BASELINE, {2: run})
        self.assertFalse(report["checks"]["reload_boot_preserves_counter"])
        self.assertFalse(report["all_checks_pass"])

    def test_win_without_increment_fails(self) -> None:
        report = probe.summarize(BASELINE, {2: reload_run(2, 2)})
        self.assertFalse(report["checks"]["reload_next_win_increments_counter"])

    def test_snapshot_frame_requires_settled_agreeing_counters(self) -> None:
        samples = {100: s(2, 1), 200: {**s(2), "counters": [2, 2, 1]}, 300: s(2)}
        self.assertEqual(probe.snapshot_frame(samples, 2), 300)
        self.assertIsNone(probe.snapshot_frame(samples, 5))


if __name__ == "__main__":
    unittest.main()
