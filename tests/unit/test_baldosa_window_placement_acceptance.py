#!/usr/bin/env python3
"""The window-placement runner fails closed on every way a restore can go wrong."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import run_baldosa_window_placement_acceptance as runner

DEFAULT = (319, 107)


def fake_game(restore=True, save=True, honour_missing=True, drift=(0, 0)):
    """A stand-in for the native game that speaks the spike's log lines."""
    def launch(exe, rom, root, smoke, label, video, timeout):
        placement = root / "window-placement.txt"
        lines, pos = [], DEFAULT
        if restore and placement.is_file():
            saved = dict(l.split("=", 1) for l in placement.read_text().splitlines()[1:])
            if saved["display_name"] != "screen":
                lines.append(f"UR_DISPLAY placement saved_display_missing name={saved['display_name']}")
                if not honour_missing:
                    pos = tuple(int(v) for v in saved["window"].split(",")[:2])
            else:
                pos = tuple(int(v) for v in saved["window"].split(",")[:2])
                pos = (pos[0] + drift[0], pos[1] + drift[1])
                lines.append(f"UR_DISPLAY placement restored display=screen fullscreen=0 "
                             f"window={pos[0]},{pos[1]}")
        mode = "report"
        if smoke.startswith("move:"):
            mode, pos = "move", tuple(int(v) for v in smoke[5:].split(","))
        lines.append(f"UR_DISPLAY_PLACEMENT_SMOKE mode={mode} window={pos[0]},{pos[1]} "
                     f"fullscreen=0 display=screen")
        if save:
            placement.write_text("ur-window-placement-v1\ndisplay_name=screen\n"
                                 "display_bounds=0,0,1280,720\n"
                                 f"window={pos[0]},{pos[1]},640,480\n")
            lines.append("UR_DISPLAY placement saved=1 display=screen")
        return "\n".join(lines) + "\n"
    return launch


class WindowPlacementRunnerTests(unittest.TestCase):
    def run_with(self, game):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            exe, rom = tmp / "game.exe", tmp / "game.sfc"
            exe.write_bytes(b"exe")
            rom.write_bytes(b"rom")
            return runner.run(exe, rom, tmp / "out", "dummy", 1, launcher=game)

    def test_restore_and_fallback_pass(self):
        receipt = self.run_with(fake_game())
        self.assertEqual(receipt["relaunched_window"], [37, 53])
        self.assertEqual(receipt["fallback_window"], list(DEFAULT))
        self.assertIn("not multi-monitor acceptance", receipt["scope"])

    def test_every_failure_is_caught(self):
        for broken in (fake_game(restore=False), fake_game(save=False),
                       fake_game(honour_missing=False), fake_game(drift=(-1, -20))):
            with self.assertRaises(ValueError):
                self.run_with(broken)

    def test_existing_output_is_never_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "x").write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "must not pre-exist"):
                runner.run(tmp / "x", tmp / "x", tmp, "dummy", 1, launcher=fake_game())


if __name__ == "__main__":
    unittest.main()
