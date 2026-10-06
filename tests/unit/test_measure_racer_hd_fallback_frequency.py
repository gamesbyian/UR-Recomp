import unittest

from tools.measure_racer_hd_fallback_frequency import build_report
from tools.summarize_racer_semantic_trace import parse_trace


def entry(player, semantic, p1, p2, p1c="0x0000", p2c="0x0000"):
    return {
        "representation_id": f"{player}-{semantic}-{p1}-{p2}",
        "player": player,
        "semantic_frame_id": semantic,
        "composition_guards": {
            "p1_primary": p1,
            "p2_primary": p2,
            "p1_companion": p1c,
            "p2_companion": p2c,
            "p1_selector": 0,
            "p2_selector": 0,
            "p1_companion_gate_word": "0x0000",
            "p2_companion_gate_word": "0x0000",
        },
    }


class RacerHdFallbackFrequencyTests(unittest.TestCase):
    def test_ranks_recurring_exact_state_ahead_of_equal_contiguous_burden(self):
        log = "\n".join([
            "UR_RACER_PRESENTATION_TRACE frame=10 p1_primary=0540 p2_primary=0543 p1_companion=0000 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0000 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=11 p1_primary=0541 p2_primary=0542 p1_companion=0000 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0000 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=12 p1_primary=0540 p2_primary=0543 p1_companion=0000 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0000 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=13 p1_primary=057C p2_primary=0547 p1_companion=0000 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0000 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=14 p1_primary=057C p2_primary=0547 p1_companion=0000 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0000 p2_gate=0000",
        ])
        registry = {"entries": [
            entry("p1", "0x0541", "0x0541", "0x0542"),
            entry("p2", "0x0542", "0x0541", "0x0542"),
        ]}
        report = build_report(parse_trace(log), registry)
        self.assertEqual(report["measurement"]["player_frame_observations"], 10)
        self.assertEqual(report["measurement"]["hd_selected_player_frames"], 2)
        self.assertEqual(report["measurement"]["original_fallback_player_frames"], 8)
        self.assertEqual(
            report["fallback_by_player_primary_semantic_id"][0],
            {"player": "p1", "semantic_frame_id": "0x0540", "player_frames": 2},
        )
        self.assertEqual(
            report["fallback_by_player_visual_context"][0],
            {
                "player": "p1",
                "semantic_frame_id": "0x0540",
                "companion": "0x0000",
                "selector": 0,
                "gate": "0x0000",
                "player_frames": 2,
                "frame_hits": 2,
                "episode_count": 2,
                "frames": [10, 12],
            },
        )
        top = report["unsupported_exact_states_ranked"][0]
        self.assertEqual(top["composition"]["p1_primary"], "0x0540")
        self.assertEqual(top["composition"]["p2_primary"], "0x0543")
        self.assertEqual(top["player_frames"], 4)
        self.assertEqual(top["episode_count"], 2)

    def test_exact_registration_removes_only_matching_player_frames(self):
        log = (
            "UR_RACER_PRESENTATION_TRACE frame=20 "
            "p1_primary=0540 p2_primary=0543 "
            "p1_companion=0D2C p2_companion=0000 "
            "p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000"
        )
        rows = parse_trace(log)
        before = build_report(rows, {"entries": []})
        after = build_report(rows, {"entries": [
            {
                **entry("p1", "0x0540", "0x0540", "0x0543", "0x0D2C"),
                "composition_guards": {
                    "p1_primary": "0x0540", "p2_primary": "0x0543",
                    "p1_companion": "0x0D2C", "p2_companion": "0x0000",
                    "p1_selector": 0, "p2_selector": 0,
                    "p1_companion_gate_word": "0x0001", "p2_companion_gate_word": "0x0000",
                },
            }
        ]})
        self.assertEqual(before["measurement"]["original_fallback_player_frames"], 2)
        self.assertEqual(after["measurement"]["original_fallback_player_frames"], 1)


if __name__ == "__main__":
    unittest.main()
