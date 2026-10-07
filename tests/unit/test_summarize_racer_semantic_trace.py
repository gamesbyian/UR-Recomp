import unittest

from tools.summarize_racer_semantic_trace import (
    build_report,
    parse_trace,
    registered_composition_coverage,
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

    def test_player_local_guard_ignores_only_opponent_fields(self):
        row = parse_trace(
            "UR_RACER_PRESENTATION_TRACE frame=10 p1_primary=04B9 p2_primary=0578 "
            "p1_companion=0000 p2_companion=0EC3 p1_selector=0000 p2_selector=0000 "
            "p1_gate=0000 p2_gate=0001"
        )[0]
        entry = {
            "semantic_frame_id": "0x04B9",
            "representation_id": "p1-local",
            "player": "p1",
            "guard_scope": "player_local",
            "registration": {
                "guard_scope_proof": {
                    "scope": "player_local",
                    "structural_basis": "players occupy disjoint object columns",
                    "empirical_basis": "multiple exact witnesses collapse to one local raster",
                    "workflow_run": 1,
                    "artifact_id": 1,
                }
            },
            "composition_guards": {
                "p1_primary": "0x04B9", "p2_primary": "0x0546",
                "p1_companion": "0x0000", "p2_companion": "0x0EB2",
                "p1_selector": 0, "p2_selector": 0,
                "p1_companion_gate_word": "0x0000",
                "p2_companion_gate_word": "0x0001",
            },
        }
        self.assertTrue(row_matches_registration(row, entry))
        row["p1_companion"] = "0x0001"
        self.assertFalse(row_matches_registration(row, entry))

    def test_registered_composition_coverage_requires_both_players(self):
        text = "\n".join([
            "UR_RACER_PRESENTATION_TRACE frame=10 p1_primary=0541 p2_primary=0540 p1_companion=0D0D p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=11 p1_primary=0541 p2_primary=0540 p1_companion=0D0D p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=12 p1_primary=0542 p2_primary=0540 p1_companion=0000 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0000 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=13 p1_primary=057E p2_primary=0544 p1_companion=0D49 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
        ])
        def entry(player, semantic, representation, p1, p2, p1c):
            return {
                "semantic_frame_id": semantic,
                "representation_id": representation,
                "player": player,
                "composition_guards": {
                    "p1_primary": p1,
                    "p2_primary": p2,
                    "p1_companion": p1c,
                    "p2_companion": "0x0000",
                    "p1_selector": 0,
                    "p2_selector": 0,
                    "p1_companion_gate_word": "0x0001",
                    "p2_companion_gate_word": "0x0000",
                },
            }
        registry = {"entries": [
            entry("p1", "0x0541", "p1-a", "0x0541", "0x0540", "0x0D0D"),
            entry("p2", "0x0540", "p2-a", "0x0541", "0x0540", "0x0D0D"),
            entry("p1", "0x057E", "p1-b", "0x057E", "0x0544", "0x0D49"),
            entry("p2", "0x0544", "p2-b", "0x057E", "0x0544", "0x0D49"),
        ]}
        coverage = registered_composition_coverage(parse_trace(text), registry)
        self.assertEqual(coverage["fully_registered_frames"], [10, 11, 13])
        self.assertEqual(coverage["fully_registered_runs"], [[10, 11], [13, 13]])
        self.assertFalse(coverage["frames"][2]["fully_registered"])
        self.assertIsNone(coverage["frames"][2]["p1_representation_id"])

    def test_registered_composition_coverage_rejects_ambiguous_player_match(self):
        row = parse_trace(
            "UR_RACER_PRESENTATION_TRACE frame=10 p1_primary=0541 p2_primary=0540 p1_companion=0D0D p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000"
        )
        entry = {
            "semantic_frame_id": "0x0541",
            "representation_id": "p1-a",
            "player": "p1",
            "composition_guards": {
                "p1_primary": "0x0541", "p2_primary": "0x0540",
                "p1_companion": "0x0D0D", "p2_companion": "0x0000",
                "p1_selector": 0, "p2_selector": 0,
                "p1_companion_gate_word": "0x0001",
                "p2_companion_gate_word": "0x0000",
            },
        }
        duplicate = dict(entry, representation_id="p1-b")
        with self.assertRaisesRegex(ValueError, "ambiguous p1 registration"):
            registered_composition_coverage(row, {"entries": [entry, duplicate]})

    def test_gap_is_not_dense(self):
        rows = parse_trace("\n".join([
            "UR_RACER_PRESENTATION_TRACE frame=10 p1_primary=0541 p2_primary=0540 p1_companion=0D0D p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
            "UR_RACER_PRESENTATION_TRACE frame=12 p1_primary=057E p2_primary=0544 p1_companion=0D49 p2_companion=0000 p1_selector=0000 p2_selector=0000 p1_gate=0001 p2_gate=0000",
        ]))
        self.assertFalse(build_report(rows)["contiguous"])


if __name__ == "__main__":
    unittest.main()
