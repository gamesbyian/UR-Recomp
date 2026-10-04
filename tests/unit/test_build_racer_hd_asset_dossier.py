import unittest

from tools.build_racer_hd_asset_dossier import (
    FIRST_AUTHORED_REPRESENTATION_ID,
    SECOND_AUTHORED_REPRESENTATION_ID,
    THIRD_AUTHORED_REPRESENTATION_ID,
    FOURTH_AUTHORED_REPRESENTATION_ID,
    FIFTH_AUTHORED_REPRESENTATION_ID,
    SIXTH_AUTHORED_REPRESENTATION_ID,
    SEVENTH_AUTHORED_REPRESENTATION_ID,
    EIGHTH_AUTHORED_REPRESENTATION_ID,
    NINTH_AUTHORED_REPRESENTATION_ID,
    TENTH_AUTHORED_REPRESENTATION_ID,
    ELEVENTH_AUTHORED_REPRESENTATION_ID,
    TWELFTH_AUTHORED_REPRESENTATION_ID,
    THIRTEENTH_AUTHORED_REPRESENTATION_ID,
    FOURTEENTH_AUTHORED_REPRESENTATION_ID,
    PENDING_ART_DECISIONS,
    RESOLVED_VISUAL_LANGUAGE,
    build_first_authored_candidate_rgba,
    build_second_authored_candidate_rgba,
    build_third_authored_candidate_rgba,
    build_fourth_authored_candidate_rgba,
    build_fifth_authored_candidate_rgba,
    build_sixth_authored_candidate_rgba,
    build_seventh_authored_candidate_rgba,
    build_eighth_authored_candidate_rgba,
    build_ninth_authored_candidate_rgba,
    build_tenth_authored_candidate_rgba,
    exact_window_rows,
    gameplay_sampled_alpha_review,
    observation_map,
    registry_by_representation,
    safe_name,
    sample_authored_0541_p1_rgba,
    sample_authored_0541_p1_companion_0d2d_rgba,
    sample_authored_0540_p1_predecessor_rgba,
    sample_authored_057f_p1_companion_0d4a_rgba,
    sample_authored_057e_p1_with_p2_0543_rgba,
    sample_authored_057d_p1_with_p2_0543_rgba,
    sample_authored_0540_p2_baseline_rgba,
    sample_authored_0541_p2_predecessor_rgba,
    sample_authored_0542_p2_rgba,
    sample_authored_0543_p2_rgba,
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
        self.assertEqual(sample_authored_0541_p1_rgba(112, 116), bytes((224, 221, 216, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(123, 90), bytes((42, 39, 32, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(128, 22), bytes((49, 45, 38, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(132, 50), bytes((232, 83, 83, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(132, 30), bytes((246, 244, 242, 255)))
        # Refinement pass 1 restores stock-supported internal structure with
        # a second fork brace and restrained six-spoke wheel detail.
        self.assertEqual(sample_authored_0541_p1_rgba(116, 88), bytes((201, 52, 52, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(110, 122), bytes((224, 221, 216, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(0, 0), bytes((0, 0, 0, 0)))

        rgba = build_first_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        self.assertGreater(
            sum(1 for i in range(3, len(rgba), 4) if rgba[i] != 0),
            1000,
        )

        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_0541_p1_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [22, 3, 39, 38],
        )
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [29, 32])

        stock = bytearray(64 * 64 * 4)
        for y in range(3, 39):
            for x in range(22, 40):
                stock[((y * 64 + x) * 4) + 3] = 255
        review = gameplay_sampled_alpha_review(rgba, bytes(stock))
        self.assertEqual(review["candidate_alpha_bounds"], [22, 3, 39, 38])
        self.assertEqual(review["candidate_contact_x2_y2"], [61, 76])
        self.assertGreater(review["alpha_iou"], 0.3)
        self.assertEqual(
            review["stock_only_pixel_count"],
            review["stock_opaque_pixels"] - review["alpha_intersection_pixels"],
        )
        self.assertEqual(
            review["candidate_only_pixel_count"],
            review["candidate_opaque_pixels"] - review["alpha_intersection_pixels"],
        )
        self.assertEqual(
            len(review["stock_only_pixels"]),
            review["stock_only_pixel_count"],
        )
        self.assertEqual(
            len(review["candidate_only_pixels"]),
            review["candidate_only_pixel_count"],
        )

    def test_second_authored_candidate_matches_predecessor_envelope(self):
        self.assertEqual(
            SECOND_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0541-p1-companion-0D2D-reference",
        )
        rgba = build_second_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        self.assertNotEqual(
            sample_authored_0541_p1_companion_0d2d_rgba(130, 10),
            bytes((0, 0, 0, 0)),
        )

        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_0541_p1_companion_0d2d_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [22, 2, 39, 38],
        )
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [29, 32])

    def test_third_authored_candidate_matches_reversed_predecessor(self):
        self.assertEqual(
            THIRD_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0540-p1-predecessor-reference",
        )
        rgba = build_third_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        self.assertNotEqual(
            sample_authored_0540_p1_predecessor_rgba(128, 120),
            bytes((0, 0, 0, 0)),
        )

        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_0540_p1_predecessor_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [23, 2, 40, 38],
        )
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [30, 33])

    def test_fourth_registration_is_context_reuse(self):
        self.assertEqual(
            FOURTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0540-p1-companion-0D2C-with-p2-0542-reference",
        )
        self.assertNotEqual(
            FOURTH_AUTHORED_REPRESENTATION_ID,
            THIRD_AUTHORED_REPRESENTATION_ID,
        )
        # Reuse deliberately has no fourth image generator: both exact
        # composition IDs consume the already-reviewed third authored asset.
        self.assertEqual(len(build_third_authored_candidate_rgba()), 256 * 256 * 4)

    def test_fifth_registration_authors_repeated_1215_1216_pose(self):
        self.assertEqual(
            FIFTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x057f-p1-with-p2-0542-companion-0D4A-reference",
        )
        self.assertEqual(len(build_fourth_authored_candidate_rgba()), 256 * 256 * 4)
        self.assertEqual(
            sample_authored_057f_p1_companion_0d4a_rgba(156, 22),
            bytes((0, 0, 0, 0)),
        )

        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_057f_p1_companion_0d4a_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [22, 2, 41, 38],
        )
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [31, 34])
        self.assertEqual(len(occupied), 329)

    def test_sixth_registration_authors_repeated_057e_pose(self):
        self.assertEqual(
            SIXTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x057E-p1-with-p2-0543-reference",
        )
        self.assertEqual(len(build_fifth_authored_candidate_rgba()), 256 * 256 * 4)
        self.assertEqual(
            sample_authored_057e_p1_with_p2_0543_rgba(150, 22),
            bytes((0, 0, 0, 0)),
        )

        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_057e_p1_with_p2_0543_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [21, 2, 42, 38],
        )
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [32, 35])

    def test_seventh_registration_authors_repeated_057d_pose(self):
        self.assertEqual(
            SEVENTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x057D-p1-adjacent-reference",
        )
        self.assertEqual(len(build_sixth_authored_candidate_rgba()), 256 * 256 * 4)
        self.assertEqual(
            sample_authored_057d_p1_with_p2_0543_rgba(146, 26),
            bytes((0, 0, 0, 0)),
        )

        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_057d_p1_with_p2_0543_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [21, 3, 43, 38],
        )
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [33, 36])

    def test_eighth_registration_authors_p2_baseline(self):
        self.assertEqual(
            EIGHTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0540-p2-sync-reference",
        )
        self.assertEqual(len(build_seventh_authored_candidate_rgba()), 256 * 256 * 4)

        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_0540_p2_baseline_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [23, 3, 40, 38],
        )
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [30, 33])

    def test_ninth_registration_reuses_p2_baseline_asset(self):
        self.assertEqual(
            NINTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0540-p2-with-p1-companion-0D2D-reference",
        )
        rgba = build_seventh_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_0540_p2_baseline_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [23, 3, 40, 38],
        )

    def test_tenth_registration_authors_p2_0541_predecessor(self):
        self.assertEqual(
            TENTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0541-p2-predecessor-reference",
        )
        self.assertEqual(len(build_eighth_authored_candidate_rgba()), 256 * 256 * 4)
        self.assertEqual(
            sample_authored_0541_p2_predecessor_rgba(94, 22),
            bytes((0, 0, 0, 0)),
        )
        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_0541_p2_predecessor_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [min(x for x, _ in occupied), min(y for _, y in occupied),
             max(x for x, _ in occupied), max(y for _, y in occupied)],
            [22, 3, 39, 38],
        )

    def test_shared_0542_p2_pose_matches_stock_geometry(self):
        self.assertEqual(
            ELEVENTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0542-p2-with-p1-companion-0D2C-reference",
        )
        self.assertEqual(
            TWELFTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0542-p2-with-p1-057F-companion-0D4A-reference",
        )
        self.assertEqual(len(build_ninth_authored_candidate_rgba()), 256 * 256 * 4)
        self.assertEqual(
            sample_authored_0542_p2_rgba(132, 84),
            bytes((37, 58, 163, 255)),
        )
        self.assertEqual(
            sample_authored_0542_p2_rgba(126, 110),
            bytes((224, 221, 216, 255)),
        )
        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_0542_p2_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [min(x for x, _ in occupied), min(y for _, y in occupied),
             max(x for x, _ in occupied), max(y for _, y in occupied)],
            [21, 4, 40, 38],
        )
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [28, 31])

    def test_shared_0543_p2_pose_matches_stock_geometry(self):
        self.assertEqual(
            THIRTEENTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0543-p2-adjacent-reference",
        )
        self.assertEqual(
            FOURTEENTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0543-p2-with-p1-057E-reference",
        )
        self.assertEqual(len(build_tenth_authored_candidate_rgba()), 256 * 256 * 4)
        self.assertEqual(
            sample_authored_0543_p2_rgba(130, 88),
            bytes((37, 58, 163, 255)),
        )
        self.assertEqual(
            sample_authored_0543_p2_rgba(122, 110),
            bytes((224, 221, 216, 255)),
        )
        occupied = []
        for ly in range(64):
            for lx in range(64):
                sx = lx * 4 + 2
                sy = ly * 4 + 2
                if sample_authored_0543_p2_rgba(sx, sy)[3] != 0:
                    occupied.append((lx, ly))
        self.assertEqual(
            [min(x for x, _ in occupied), min(y for _, y in occupied),
             max(x for x, _ in occupied), max(y for _, y in occupied)],
            [20, 4, 40, 38],
        )
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [26, 31])

    def test_safe_name_is_path_stable(self):
        self.assertEqual(safe_name("racer / 0x0541:p1"), "racer-0x0541-p1")


if __name__ == "__main__":
    unittest.main()
