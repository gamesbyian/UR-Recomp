import unittest

from tools.summarize_racer_semantic_trace import (
    build_report,
    parse_trace,
    row_matches_registration,
)


class RacerSemanticTraceTests(unittest.TestCase):
    def test_dense_trace_builds_runs_and_transitions(self):
        text = "\n".join([
            "UR_RACER_PRESENTATION_TRACE frame=10 p1_primary=0541 p2_primary=0540 p1_companion=0D0D p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=11 p1_primary=0541 p2_primary=0544 p1_companion=0D0D p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=12 p1_primary=057E p2_primary=0544 p1_companion=0D49 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
        ])
        rows = parse_trace(text)
        report = build_report(rows)
        self.assertTrue(report["contiguous"])
        self.assertEqual(report["frame_window"], [10, 12])
        self.assertEqual(
            report["players"]["p1"]["runs"],
            [
                {"start_frame": 10, "end_frame": 11, "frames": 2, "semantic_frame_id": "0x0541"},
                {"start_frame": 12, "end_frame": 12, "frames": 1, "semantic_frame_id": "0x057E"},
            ],
        )
        self.assertIn(
            {"from": "0x0541", "to": "0x057E", "count": 1},
            report["players"]["p1"]["transitions"],
        )
        self.assertFalse(report["raster_identity_authority"])


    def test_registry_neighborhoods_use_full_composition_guards(self):
        text = "\n".join([
            "UR_RACER_PRESENTATION_TRACE frame=10 p1_primary=0541 p2_primary=0540 p1_companion=0D0D p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=11 p1_primary=0541 p2_primary=0540 p1_companion=0D0D p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=12 p1_primary=0542 p2_primary=0540 p1_companion=0000 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0000 p2_gate=0000",
        ])
        registry = {
            "entries": [{
                "semantic_frame_id": "0x0541",
                "representation_id": "p1-0541",
                "player": "p1",
                "composition_guards": {
                    "p1_primary": "0x0541",
                    "p2_primary": "0x0540",
                    "p1_companion": "0x0D0D",
                    "p2_companion": "0x0000",
                    "p1_selector": 0,
                    "p2_selector": 0,
                    "p1_companion_gate_word": "0x0001",
                    "p2_companion_gate_word": "0x0000",
                },
            }]
        }
        rows = parse_trace(text)
        self.assertTrue(row_matches_registration(rows[0], registry["entries"][0]))
        report = build_report(rows, registry)
        n = report["registered_state_neighborhoods"][0]
        self.assertEqual(n["hit_frames"], [10, 11])
        self.assertEqual(n["previous_primary_counts"], {"0x0541": 1})
        self.assertEqual(n["next_primary_counts"], {"0x0541": 1, "0x0542": 1})

    def test_gap_is_not_dense(self):
        rows = parse_trace("\n".join([
            "UR_RACER_PRESENTATION_TRACE frame=10 p1_primary=0541 p2_primary=0540 p1_companion=0D0D p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=12 p1_primary=057E p2_primary=0544 p1_companion=0D49 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
        ]))
        self.assertFalse(build_report(rows)["contiguous"])


if __name__ == "__main__":
    unittest.main()
