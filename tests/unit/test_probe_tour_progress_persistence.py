import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_tour_progress_persistence as probe  # noqa: E402


def flags(n):
    return [1] * n + [0] * (5 - n)


def s(counter, in_race=0, menu=0, track=0, tour=None):
    return {"menu": menu, "track": track, "in_race": in_race, "tour_flags": flags(counter if tour is None else tour),
            "counters": [counter] * 3, "nonzero_medals_rows_0_7": 0}


BASELINE = {750: s(0), 1000: s(0, 1), 3000: s(1), 8500: s(2), 12000: s(3)}


def reload_run(start, after):
    return {"input_counter": start, "input_tour_flags": flags(start), "boot_diff": ["0x0742"],
            "samples": {300: s(start), 750: s(start, tour=0), 1000: s(start, 1, tour=0), 3250: s(after, tour=1)}}


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
        self.assertFalse(report["checks"]["reload_next_race_increments_counter"])

    def test_tour_flags_surviving_rider_select_fail(self) -> None:
        run = reload_run(2, 3)
        run["samples"][1000] = s(2, 1)
        report = probe.summarize(BASELINE, {2: run})
        self.assertTrue(report["checks"]["reload_boot_preserves_tour_flags"])
        self.assertFalse(report["checks"]["reload_rider_select_clears_tour_flags"])

    def test_tour_flags_lost_at_boot_fail(self) -> None:
        run = reload_run(2, 3)
        run["samples"][300] = s(2, tour=0)
        report = probe.summarize(BASELINE, {2: run})
        self.assertFalse(report["checks"]["reload_boot_preserves_tour_flags"])

    def test_snapshot_frame_requires_settled_agreeing_counters(self) -> None:
        samples = {100: s(2, 1), 200: {**s(2), "counters": [2, 2, 1]}, 300: s(2)}
        self.assertEqual(probe.snapshot_frame(samples, 2), 300)
        self.assertIsNone(probe.snapshot_frame(samples, 5))


if __name__ == "__main__":
    unittest.main()
