import unittest

from tools.build_racer_hd_asset_dossier import (
    FIRST_AUTHORED_REPRESENTATION_ID,
    PENDING_ART_DECISIONS,
    RESOLVED_VISUAL_LANGUAGE,
    build_first_authored_candidate_rgba,
    exact_window_rows,
    observation_map,
    registry_by_representation,
    safe_name,
    sample_authored_0541_p1_rgba,
    transition_context,
)


def row(frame, p1, p2, fully=True):
    return {
        "frame": frame,
        "fully_registered": fully,
        "p1_representation_id": p1,
        "p2_representation_id": p2,
    }


class RacerHdAssetDossierTests(unittest.TestCase):
    def test_exact_window_requires_every_frame_and_both_players(self):
        trace = {
            "registered_composition_coverage": {
                "frames": [
                    row(10, "p1-a", "p2-a"),
                    row(11, "p1-a", "p2-b"),
                    row(12, "p1-b", "p2-b"),
                ]
            }
        }
        rows = exact_window_rows(trace, 10, 12)
        self.assertEqual([x["frame"] for x in rows], [10, 11, 12])

        gap = {
            "registered_composition_coverage": {
                "frames": [row(10, "p1-a", "p2-a"), row(12, "p1-b", "p2-b")]
            }
        }
        with self.assertRaisesRegex(ValueError, "not exact/contiguous"):
            exact_window_rows(gap, 10, 12)

        incomplete = {
            "registered_composition_coverage": {
                "frames": [
                    row(10, "p1-a", "p2-a"),
                    row(11, "p1-a", "p2-b", fully=False),
                    row(12, "p1-b", "p2-b"),
                ]
            }
        }
        with self.assertRaisesRegex(ValueError, "not fully registered"):
            exact_window_rows(incomplete, 10, 12)

    def test_observation_map_and_transition_context_use_observed_order(self):
        rows = [
            row(10, "p1-a", "p2-a"),
            row(11, "p1-a", "p2-a"),
            row(12, "p1-b", "p2-a"),
            row(13, "p1-b", "p2-b"),
            row(14, "p1-a", "p2-b"),
        ]
        observed = observation_map(rows)
        self.assertEqual(observed["p1-a"]["frames"], [10, 11, 14])
        self.assertEqual(observed["p2-a"]["frames"], [10, 11, 12])

        context = transition_context(rows, "p1-b", "p1")
        self.assertEqual(
            context["previous_representations"],
            [{"representation_id": "p1-a", "entry_frames": [12]}],
        )
        self.assertEqual(
            context["next_representations"],
            [{"representation_id": "p1-a", "exit_frames": [13]}],
        )

    def test_observation_map_rejects_cross_player_representation(self):
        rows = [
            row(10, "shared", "p2-a"),
            row(11, "p1-b", "shared"),
        ]
        with self.assertRaisesRegex(ValueError, "appears for both players"):
            observation_map(rows)

    def test_registry_ids_must_be_unique(self):
        registry = {
            "entries": [
                {"representation_id": "same"},
                {"representation_id": "same"},
            ]
        }
        with self.assertRaisesRegex(ValueError, "duplicate representation_id"):
            registry_by_representation(registry)

    def test_visual_language_closes_lighting_and_edge_policy(self):
        self.assertIn("lighting_space", RESOLVED_VISUAL_LANGUAGE)
        self.assertIn("edge_treatment", RESOLVED_VISUAL_LANGUAGE)
        self.assertNotIn("lighting_direction_and_environment", PENDING_ART_DECISIONS)
        self.assertNotIn("outline_and_edge_treatment", PENDING_ART_DECISIONS)
        self.assertIn("material_classes", RESOLVED_VISUAL_LANGUAGE)
        self.assertIn("cast_shadow_policy", RESOLVED_VISUAL_LANGUAGE)
        self.assertIn("micro_detail_policy", RESOLVED_VISUAL_LANGUAGE)
        self.assertNotIn("material_interpretation", PENDING_ART_DECISIONS)
        self.assertNotIn("shadow_behavior", PENDING_ART_DECISIONS)
        self.assertNotIn(
            "micro_detail_budget_at_4k_1440p_1080p_and_split_screen",
            PENDING_ART_DECISIONS,
        )
        self.assertIn("specular_highlight_policy", RESOLVED_VISUAL_LANGUAGE)
        self.assertEqual(PENDING_ART_DECISIONS, [])

    def test_first_authored_candidate_material_regions(self):
        self.assertEqual(
            FIRST_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0541-p1-sync-reference",
        )
        self.assertEqual(sample_authored_0541_p1_rgba(100, 100), bytes((246, 244, 242, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(100, 90), bytes((64, 60, 53, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(108, 36), bytes((75, 71, 65, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(115, 51), bytes((232, 83, 83, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(0, 0), bytes((0, 0, 0, 0)))

        rgba = build_first_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        self.assertGreater(
            sum(1 for i in range(3, len(rgba), 4) if rgba[i] != 0),
            1000,
        )

    def test_safe_name_is_path_stable(self):
        self.assertEqual(safe_name("racer / 0x0541:p1"), "racer-0x0541-p1")


if __name__ == "__main__":
    unittest.main()
