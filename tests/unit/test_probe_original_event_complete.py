"""QA-01 full-result producer: synthetic contract tests, NEVER real witnesses."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as target


def source_states(entry: int, result: int, track: int, menu: int, tally: bool = False):
    out = {}
    for f in range(entry - 1, result + 16):
        m = menu if f >= result else 0x16
        if tally and result - 60 <= f < result:
            m = 0x2F
        out[f] = {"track": track, "in_race": 1 if entry <= f < result - 30 else 0,
                  "menu": m}
    return out


def capture(menu=0xBC, text=None):
    if text is None:
        text = ["PLAYER", "TOTAL", "MIKE", "1:16.46"]
    return {"samples": [
                {"relative_frame": 0, "p1_x": 20, "p1_laps": 4},
                {"relative_frame": 218, "p1_x": 40, "p1_laps": 3},
                {"relative_frame": 1721, "p1_x": 80, "p1_laps": 2},
            ],
            "result": {"menu": menu}, "onset": {"menu": menu},
            "result_text": {"final": text, "onset": text}}


class CompleteEventProducerTests(unittest.TestCase):
    def test_source_anchors_come_from_real_state_change_not_guess(self):
        event = target.source_event(source_states(3190, 8353, 1, 0xBC),
                                    1, 0xBC)
        self.assertEqual(event["original_entry_frame"], 3190)
        self.assertEqual(event["original_result_frame"], 8353)
        self.assertEqual(event["source_active_frames_to_result"], 5163)
        with self.assertRaisesRegex(target.CompleteEventError, "never demonstrated"):
            target.source_event(source_states(3190, 8353, 1, 0xBC), 3, 0x99)
        with self.assertRaisesRegex(target.CompleteEventError, "never demonstrated"):
            target.source_event(source_states(3190, 8353, 1, 0xBC), 1, 0x99)

    def test_stunt_requires_two_distinct_original_result_phases(self):
        states = source_states(8620, 11985, 2, 0x18, tally=True)
        event = target.source_event(states, 2, 0x18)
        self.assertEqual(event["source_stunt_tally_frame"], 11925)
        with self.assertRaisesRegex(target.CompleteEventError, "missing prior"):
            target.source_event(source_states(8620, 11985, 2, 0x18), 2, 0x18)

    def test_stock_route_selection_uses_original_menu_and_no_guest_poke(self):
        for case, (slot, _, menu, kind) in target.CASES.items():
            script = target.stock_crawler_script(slot)
            self.assertIn(f"until 009B == {slot - 1:02X} 600", script)
            self.assertEqual(script.count("press down 2"), slot - 1)
            self.assertEqual(script.count("dump race-entered"), 1)
            self.assertNotIn("poke ", script)
            frames = target.sample_frames(case, 5163)
            self.assertIn(0, frames)
            self.assertIn(64, frames)
            self.assertLess(max(frames), 5163 - 200)
            replay = target.replay_script(slot, menu, frames, kind == "stunt")
            self.assertIn(f"until 009F == {menu:02X} 9000", replay)
            self.assertEqual(replay.count("dump result-stable"), 1)
            self.assertNotIn("poke ", replay)
        self.assertIn("dump result-tally", target.replay_script(
            3, 0x18, target.sample_frames("bowl", 3500), True))
        self.assertNotIn("dump result-tally", target.replay_script(
            2, 0xBC, target.sample_frames("zoom-zoo", 5163), False))
        with self.assertRaisesRegex(target.CompleteEventError, "only"):
            target.stock_crawler_script(1)

    def test_result_parity_requires_score_text_and_all_guest_samples(self):
        ref = capture()
        nat = capture()
        self.assertTrue(target.diagnose(ref, nat, 0xBC, False)["paired_event_candidate"])
        nat["samples"][1]["p1_laps"] = 4
        mismatch = target.diagnose(ref, nat, 0xBC, False)
        self.assertEqual(mismatch["first_sample_disagreement"]["relative_frame"], 218)
        self.assertEqual(mismatch["first_sample_disagreement"]["fields"], ["p1_laps"])
        self.assertFalse(mismatch["paired_event_candidate"])
        nat = capture(text=["MIKE", "1:17.46"])
        self.assertFalse(target.diagnose(ref, nat, 0xBC, False)["paired_event_candidate"])
        nat = capture(menu=0x99)
        self.assertFalse(target.diagnose(ref, nat, 0xBC, False)["both_reached_terminal_menu"])

    def test_stunt_idle_zero_score_cannot_pass_scored_result(self):
        ref = capture(0x18, ["BOWL", "MIKE", ": 0"])
        nat = capture(0x18, ["BOWL", "MIKE", ": 0"])
        self.assertFalse(target.diagnose(ref, nat, 0x18, True)["stunt_positive_score_visible"])
        self.assertFalse(target.diagnose(ref, nat, 0x18, True)["paired_event_candidate"])
        ref = capture(0x18, ["BOWL", "MIKE", ": 764"])
        nat = capture(0x18, ["BOWL", "MIKE", ": 764"])
        self.assertTrue(target.diagnose(ref, nat, 0x18, True)["paired_event_candidate"])

    def test_bounded_samples_include_original_circuit_changes(self):
        frames = target.sample_frames("zoom-zoo", 5163)
        for original_frame in (218, 604, 841, 1532, 1721):
            self.assertIn(original_frame, frames)
        self.assertGreater(len(frames), len(target.INITIAL_FRAMES))
        with self.assertRaisesRegex(target.CompleteEventError, "too short"):
            target.sample_frames("bowl", 200)


if __name__ == "__main__":
    unittest.main()
