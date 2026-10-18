"""ROM-free source-sampled result assertion consistency, not event admission."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_event_result_gate_audit as source


def fixture(case: str) -> dict:
    menu = source.COURSE_RESULT_MENU[case]
    laps = [3, 3, 2, 2, 1, 0, 0, 0] if case == "zoom-zoo" else [2] * 8
    final = ["MIKE", ": 123" if case == "bowl" else "1:08.81"]
    guest = {
        "samples": [{"relative_frame": i, "p1_laps": lap}
                    for i, lap in enumerate(laps)],
        "onset": {"menu": menu, "in_race": 0x3C, "p1_laps": 0},
        "result": {"menu": menu, "in_race": 0x3C, "p1_laps": 0},
        "result_text": {"final": final, "onset": final},
    }
    report = {"name": case, "reference": guest, "native": copy.deepcopy(guest)}
    report["comparison"] = source.recompute(report)
    return report


class SourceGateAuditTest(unittest.TestCase):
    def test_each_existing_event_family_recomputes_original_producer_gates(self):
        for case in source.COURSE_RESULT_MENU:
            with self.subTest(case=case):
                original = fixture(case)
                self.assertTrue(all(source.validate(original).values()))

    def test_source_guest_terminal_menu_cannot_be_forged(self):
        data = fixture("switcher")
        data["native"]["result"]["menu"] = 0x18
        with self.assertRaisesRegex(ValueError, "both_reached_terminal_menu"):
            source.validate(data)
        data["comparison"]["both_reached_terminal_menu"] = False
        self.assertFalse(source.validate(data)["both_reached_terminal_menu"])

    def test_final_and_intermediate_result_text_gates_rederived_independently(self):
        for gate, changed in (
            ("rendered_result_and_score_text_matched", {"final": ["MIKE", "2:03.22"], "onset": ["MIKE", "1:08.81"]}),
            ("intermediate_result_text_matched", {"final": ["MIKE", "1:08.81"], "onset": ["different"]}),
        ):
            with self.subTest(gate=gate):
                data = fixture("switcher")
                data["native"]["result_text"] = changed
                with self.assertRaisesRegex(ValueError, gate):
                    source.validate(data)

    def test_stunt_score_missing_or_opponent_only_is_not_positive_mike(self):
        data = fixture("bowl")
        data["reference"]["result_text"]["final"] = ["OPPONENT", ": 500", "MIKE", ": 0"]
        with self.assertRaisesRegex(ValueError, "rendered_result"):
            source.validate(data)
        data["native"]["result_text"]["final"] = ["OPPONENT", ": 500", "MIKE", ": 0"]
        with self.assertRaisesRegex(ValueError, "stunt_positive_score_visible"):
            source.validate(data)

    def test_multi_lap_decrements_and_final_zero_remain_strict(self):
        data = fixture("zoom-zoo")
        data["reference"]["samples"][2]["p1_laps"] = 3
        data["reference"]["samples"][4]["p1_laps"] = 2
        data["reference"]["samples"][5]["p1_laps"] = 2
        data["reference"]["samples"][6]["p1_laps"] = 2
        data["reference"]["samples"][7]["p1_laps"] = 2
        with self.assertRaisesRegex(ValueError, "circuit_multiple_lap"):
            source.validate(data)
        data = fixture("zoom-zoo")
        data["reference"]["result"]["p1_laps"] = 1
        with self.assertRaisesRegex(ValueError, "circuit_zero_remaining"):
            source.validate(data)

    def test_false_terminal_state_does_not_became_positive(self):
        data = fixture("bowl")
        data["native"]["result"]["in_race"] = 1
        with self.assertRaisesRegex(ValueError, "result_outside_active"):
            source.validate(data)
        data["comparison"]["result_outside_active_race_in_both_guests"] = False
        self.assertFalse(source.validate(data)["result_outside_active_race_in_both_guests"])


if __name__ == "__main__":
    unittest.main()
