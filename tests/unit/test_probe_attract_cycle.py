import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import probe_attract_cycle as probe  # noqa: E402


def timeline(spans):
    """spans: list of (length, menu, in_race, track, tour_row)."""
    states, f = {}, 0
    for length, menu, race, track, tour in spans:
        for _ in range(length):
            states[f] = {"menu": menu, "in_race": race, "track": track, "tour_row": tour}
            f += 1
    return states


class AttractCycleTests(unittest.TestCase):
    def test_frame_states_from_trace(self) -> None:
        lines = [json.dumps({"f": 1, "adr": "0x0009f", "old": "0x00", "val": "0xd7"}),
                 json.dumps({"f": 3, "adr": "0x00313", "old": "0x00", "val": "0x01"})]
        states = probe.frame_states(lines)
        self.assertEqual(states[2]["menu"], 0xD7)
        self.assertEqual(states[2]["in_race"], 0)
        self.assertEqual(states[3]["in_race"], 1)

    def test_segment_ignores_scratch_d7_and_measures_cycle(self) -> None:
        one_cycle = [(500, 0xD7, 0, 0, 0), (100, 0x84, 0, 0, 0), (2, 0xD7, 0, 0, 0),  # scratch blip
                     (50, 0x16, 0, 0, 0), (200, 0x00, 1, 1, 0), (20, 0x84, 1, 1, 0)]
        states = timeline(one_cycle + [(40, 0xD7, 0, 1, 0)] + one_cycle[1:] + [(40, 0xD7, 0, 3, 0)])
        cycles = probe.segment(states)
        self.assertEqual(len(cycles), 2)
        self.assertEqual(cycles[0]["idle_before_title_frames"], 500)
        self.assertEqual(cycles[0]["demo_race_frames"], 200)
        self.assertEqual(cycles[0]["track"], 1)


if __name__ == "__main__":
    unittest.main()
