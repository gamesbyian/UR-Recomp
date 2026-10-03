import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_result_screens as probe  # noqa: E402


def timeline(spans):
    states, f = {}, 0
    for length, menu in spans:
        for _ in range(length):
            states[f] = {"menu": menu, "in_race": 0, "track": 0, "tour_row": 0}
            f += 1
    return states


class ResultScreenTests(unittest.TestCase):
    def test_result_runs_find_stable_results_and_next_menu(self) -> None:
        states = timeline([(50, 0x00), (30, 0x84), (3, 0xBC), (16, 0xBC), (2, 0x77), (40, 0xF6)])
        runs = probe.result_runs(states)
        self.assertEqual([(r["menu"], r["next_menu"]) for r in runs], [(0xBC, 0xF6)])
        self.assertEqual(runs[0]["state"], "RESULT_CIRCUIT")

    def test_short_blips_are_ignored(self) -> None:
        states = timeline([(50, 0x00), (3, 0x18), (40, 0xF6)])
        self.assertEqual(probe.result_runs(states), [])


if __name__ == "__main__":
    unittest.main()
