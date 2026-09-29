from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from controller_input import ControllerRun
from replay_input_mesen import buttons_for_mask, replay


class FakeMesen:
    def __init__(self):
        self.frame = 0
        self.calls: list[tuple[str, dict]] = []

    def tool(self, name, **kwargs):
        self.calls.append((name, kwargs))
        if name == "input.set":
            return {"ok": True}
        if name == "run.step_frames":
            self.frame += kwargs["frames"]
            return {"status": {"frame": self.frame}}
        raise AssertionError(name)


class ReplayInputMesenTests(unittest.TestCase):
    def test_buttons_for_mask(self):
        self.assertEqual(
            buttons_for_mask(0x080 | 0x001 | 0x400),
            {"b": True, "right": True, "l": True},
        )

    def test_replay_drives_port_zero_and_one_independently(self):
        fake = FakeMesen()
        replay(fake, [ControllerRun(0, 2, 0x080, 0x040)], 3)

        input_calls = [call for call in fake.calls if call[0] == "input.set"]
        self.assertEqual(
            input_calls[0],
            ("input.set", {"port": 0, "subport": 0, "buttons": {"right": True}}),
        )
        self.assertEqual(
            input_calls[1],
            ("input.set", {"port": 1, "subport": 0, "buttons": {"left": True}}),
        )
        self.assertIn(
            ("input.set", {"port": 0, "subport": 0, "buttons": {}}),
            input_calls,
        )
        self.assertIn(
            ("input.set", {"port": 1, "subport": 0, "buttons": {}}),
            input_calls,
        )
        self.assertEqual(fake.frame, 3)

    def test_cross_player_staggered_runs(self):
        fake = FakeMesen()
        replay(
            fake,
            [
                ControllerRun(0, 2, 0x080, 0),
                ControllerRun(1, 2, 0, 0x001),
            ],
            3,
        )
        self.assertIn(
            ("input.set", {"port": 1, "subport": 0, "buttons": {"b": True}}),
            fake.calls,
        )


if __name__ == "__main__":
    unittest.main()
