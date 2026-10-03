import unittest

from tools.build_racer_hd_asset_dossier import (
    exact_window_rows,
    observation_map,
    registry_by_representation,
    safe_name,
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

    def test_safe_name_is_path_stable(self):
        self.assertEqual(safe_name("racer / 0x0541:p1"), "racer-0x0541-p1")


if __name__ == "__main__":
    unittest.main()
