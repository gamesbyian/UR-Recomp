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
    FIFTEENTH_AUTHORED_REPRESENTATION_ID,
    SIXTEENTH_AUTHORED_REPRESENTATION_ID,
    SEVENTEENTH_AUTHORED_REPRESENTATION_ID,
    EIGHTEENTH_AUTHORED_REPRESENTATION_ID,
    NINETEENTH_AUTHORED_REPRESENTATION_ID,
    TWENTIETH_AUTHORED_REPRESENTATION_ID,
    TWENTY_FIRST_AUTHORED_REPRESENTATION_ID,
    TWENTY_SECOND_AUTHORED_REPRESENTATION_ID,
    THIRTY_FIFTH_AUTHORED_REPRESENTATION_ID,
    THIRTY_SEVENTH_AUTHORED_REPRESENTATION_ID,
    THIRTY_EIGHTH_AUTHORED_REPRESENTATION_ID,
    THIRTY_NINTH_AUTHORED_REPRESENTATION_ID,
    FORTIETH_AUTHORED_REPRESENTATION_ID,
    FORTY_FIRST_AUTHORED_REPRESENTATION_ID,
    FORTY_SECOND_AUTHORED_REPRESENTATION_ID,
    FORTY_THIRD_AUTHORED_REPRESENTATION_ID,
    FORTY_FOURTH_AUTHORED_REPRESENTATION_ID,
    FORTY_FIFTH_AUTHORED_REPRESENTATION_ID,
    FORTY_SIXTH_AUTHORED_REPRESENTATION_ID,
    FORTY_SEVENTH_AUTHORED_REPRESENTATION_ID,
    FORTY_EIGHTH_AUTHORED_REPRESENTATION_ID,
    FORTY_NINTH_AUTHORED_REPRESENTATION_ID,
    FIFTIETH_AUTHORED_REPRESENTATION_ID,
    FIFTY_FIRST_AUTHORED_REPRESENTATION_ID,
    FIFTY_SECOND_AUTHORED_REPRESENTATION_ID,
    FIFTY_THIRD_AUTHORED_REPRESENTATION_ID,
    FIFTY_FOURTH_AUTHORED_REPRESENTATION_ID,
    PENDING_ART_DECISIONS,
    RESOLVED_VISUAL_LANGUAGE,
    authored_candidate_rgba_for_entry,
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
    build_eleventh_authored_candidate_rgba,
    build_twelfth_authored_candidate_rgba,
    build_thirteenth_authored_candidate_rgba,
    build_fourteenth_authored_candidate_rgba,
    build_fifteenth_authored_candidate_rgba,
    build_sixteenth_authored_candidate_rgba,
    build_nineteenth_authored_candidate_rgba,
    build_twentieth_authored_candidate_rgba,
    build_twenty_first_authored_candidate_rgba,
    build_twenty_second_authored_candidate_rgba,
    build_twenty_third_authored_candidate_rgba,
    build_twenty_fourth_authored_candidate_rgba,
    build_twenty_fifth_authored_candidate_rgba,
    build_twenty_sixth_authored_candidate_rgba,
    build_twenty_seventh_authored_candidate_rgba,
    build_twenty_eighth_authored_candidate_rgba,
    build_twenty_ninth_authored_candidate_rgba,
    build_thirtieth_authored_candidate_rgba,
    build_thirty_first_authored_candidate_rgba,
    build_thirty_second_authored_candidate_rgba,
    build_thirty_third_authored_candidate_rgba,
    build_thirty_fourth_authored_candidate_rgba,
    build_thirty_fifth_authored_candidate_rgba,
    build_thirty_sixth_authored_candidate_rgba,
    build_thirty_seventh_authored_candidate_rgba,
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
    sample_authored_057e_p1_companion_0d69_rgba,
    sample_authored_0544_p2_rgba,
    sample_authored_057c_p1_fifth_family_rgba,
    sample_authored_0544_p1_frequency_rgba,
    sample_authored_0578_p2_frequency_rgba,
    sample_authored_04b9_p1_broader_rgba,
    sample_authored_0239_p1_broader_rgba,
    sample_authored_0439_p1_broader_rgba,
    sample_authored_0039_p1_broader_rgba,
    sample_authored_00b9_p1_broader_rgba,
    sample_authored_02b9_p1_broader_rgba,
    sample_authored_01b9_p1_broader_rgba,
    sample_authored_0139_p1_broader_rgba,
    sample_authored_0539_p1_broader_rgba,
    sample_authored_05b9_p1_broader_rgba,
    sample_authored_03b9_p1_broader_rgba,
    sample_authored_0339_p1_broader_rgba,
    sample_authored_0379_p1_broader_rgba,
    sample_authored_05f9_p1_broader_rgba,
    sample_authored_0546_p2_0eb2_broader_rgba,
    sample_authored_03f9_p1_broader_rgba,
    sample_authored_0543_p1_third_family_rgba,
    sample_authored_0540d2c_p2_third_family_rgba,
    sample_authored_0542_p1_third_family_rgba,
    sample_authored_0541d2d_p2_third_family_rgba,
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

    def test_single_player_window_requires_only_selected_player(self):
        trace = {
            "registered_composition_coverage": {
                "frames": [
                    row(10, "p1-local", None, fully=False),
                    row(11, "p1-local", None, fully=False),
                ]
            }
        }
        rows = exact_window_rows(trace, 10, 11, ("p1",))
        self.assertEqual([x["frame"] for x in rows], [10, 11])
        observed = observation_map(rows, ("p1",))
        self.assertEqual(observed["p1-local"]["frames"], [10, 11])
        with self.assertRaisesRegex(ValueError, "not fully registered"):
            exact_window_rows(trace, 10, 11)

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
        self.assertEqual(sample_authored_0541_p1_rgba(112, 116), bytes((0, 0, 0, 0)))
        self.assertEqual(sample_authored_0541_p1_rgba(143, 116), bytes((249, 248, 247, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(123, 122), bytes((224, 221, 216, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(123, 90), bytes((42, 39, 32, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(128, 22), bytes((49, 45, 38, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(118, 28), bytes((41, 37, 29, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(118, 31), bytes((25, 23, 17, 255)))
        # The shipping-approved crown integration lets the neck/frame
        # member shading continue through the junction instead of overpainting
        # this boundary pixel with the former collar highlight.
        self.assertEqual(sample_authored_0541_p1_rgba(132, 50), bytes((201, 52, 52, 255)))
        self.assertEqual(sample_authored_0541_p1_rgba(132, 30), bytes((159, 153, 142, 255)))
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

    def test_generic_authored_asset_reuse_resolves_canonical_source(self):
        entry = {
            "representation_id": "measured-reuse",
            "authored_candidate": {
                "reused_from_representation_id": FOURTH_AUTHORED_REPRESENTATION_ID,
            },
        }
        rgba, generator, sampler = authored_candidate_rgba_for_entry(entry)
        self.assertEqual(rgba, build_third_authored_candidate_rgba())
        self.assertIn("build_third_authored_candidate_rgba", generator)
        self.assertEqual(sampler, "sample_racer_hd_authored_0540_p1_predecessor")

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
        self.assertEqual(len(occupied), 321)

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


    def test_second_family_1305_1306_authored_geometry(self):
        self.assertEqual(FIFTEENTH_AUTHORED_REPRESENTATION_ID, "ordinary-racer-0x057E-p1-sync-reference")
        self.assertEqual(SIXTEENTH_AUTHORED_REPRESENTATION_ID, "ordinary-racer-0x057E-p1-companion-0D69-reference")
        self.assertEqual(SEVENTEENTH_AUTHORED_REPRESENTATION_ID, "ordinary-racer-0x0544-p2-sync-reference")
        self.assertEqual(EIGHTEENTH_AUTHORED_REPRESENTATION_ID, "ordinary-racer-0x0544-p2-with-p1-companion-0D69-reference")
        self.assertEqual(len(build_eleventh_authored_candidate_rgba()), 256 * 256 * 4)
        self.assertEqual(len(build_twelfth_authored_candidate_rgba()), 256 * 256 * 4)

        for sampler, expected_bounds, expected_bottom in (
            (sample_authored_057e_p1_companion_0d69_rgba, [22, 2, 42, 38], [32, 35]),
            (sample_authored_0544_p2_rgba, [19, 5, 41, 38], [25, 30]),
        ):
            occupied = [
                (lx, ly)
                for ly in range(64)
                for lx in range(64)
                if sampler(lx * 4 + 2, ly * 4 + 2)[3] != 0
            ]
            self.assertEqual(
                [min(x for x, _ in occupied), min(y for _, y in occupied),
                 max(x for x, _ in occupied), max(y for _, y in occupied)],
                expected_bounds,
            )
            bottom = [x for x, y in occupied if y == 38]
            self.assertEqual([min(bottom), max(bottom)], expected_bottom)


    def test_third_family_uses_exact_opposite_player_geometry(self):
        self.assertEqual(
            NINETEENTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0543-p1-third-family-hold-reference",
        )
        self.assertEqual(
            TWENTIETH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0540-p2-third-family-hold-0D2C-reference",
        )
        self.assertEqual(
            TWENTY_FIRST_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0542-p1-third-family-recovery-reference",
        )
        self.assertEqual(
            TWENTY_SECOND_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0541-p2-third-family-recovery-0D2D-reference",
        )
        for built in (
            build_thirteenth_authored_candidate_rgba(),
            build_fourteenth_authored_candidate_rgba(),
            build_fifteenth_authored_candidate_rgba(),
            build_sixteenth_authored_candidate_rgba(),
        ):
            self.assertEqual(len(built), 256 * 256 * 4)

        pairs = (
            (sample_authored_0543_p1_third_family_rgba, sample_authored_0543_p2_rgba),
            (sample_authored_0540d2c_p2_third_family_rgba, sample_authored_0540_p1_predecessor_rgba),
            (sample_authored_0542_p1_third_family_rgba, sample_authored_0542_p2_rgba),
            (sample_authored_0541d2d_p2_third_family_rgba, sample_authored_0541_p1_companion_0d2d_rgba),
        )
        for target, source in pairs:
            for ly in range(64):
                for lx in range(64):
                    x, y = lx * 4 + 2, ly * 4 + 2
                    self.assertEqual(target(x, y)[3], source(x, y)[3])

        # Geometry and neutral materials remain identical, while frame color
        # is deliberately swapped to the target player's established palette.
        self.assertEqual(
            sample_authored_0543_p1_third_family_rgba(130, 88),
            bytes((163, 37, 37, 255)),
        )
        self.assertEqual(
            sample_authored_0542_p1_third_family_rgba(132, 84),
            bytes((163, 37, 37, 255)),
        )
        self.assertEqual(
            sample_authored_0540d2c_p2_third_family_rgba(128, 84),
            bytes((37, 58, 163, 255)),
        )

    def test_fifth_family_057c_authored_geometry(self):
        self.assertEqual(
            THIRTY_FIFTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x057C-p1-fifth-family-0540-reference",
        )
        self.assertEqual(
            len(build_nineteenth_authored_candidate_rgba()),
            256 * 256 * 4,
        )
        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_057c_p1_fifth_family_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        bounds = [
            min(x for x, _ in occupied),
            min(y for _, y in occupied),
            max(x for x, _ in occupied),
            max(y for _, y in occupied),
        ]
        self.assertEqual(bounds, [20, 3, 44, 38])
        bottom = [x for x, y in occupied if y == 38]
        self.assertEqual([min(bottom), max(bottom)], [34, 37])

    def test_measured_frequency_family_geometry_and_palette_reuse(self):
        self.assertEqual(
            THIRTY_SEVENTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0544-p1-frequency-0578-reference",
        )
        self.assertEqual(
            THIRTY_EIGHTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0578-p2-frequency-0544-reference",
        )
        self.assertEqual(len(build_twentieth_authored_candidate_rgba()), 256 * 256 * 4)
        self.assertEqual(len(build_twenty_first_authored_candidate_rgba()), 256 * 256 * 4)

        # The P1 0544 asset is exactly the approved P2 geometry with only the
        # established frame-material color transform.
        for ly in range(64):
            for lx in range(64):
                x, y = lx * 4 + 2, ly * 4 + 2
                self.assertEqual(
                    sample_authored_0544_p1_frequency_rgba(x, y)[3],
                    sample_authored_0544_p2_rgba(x, y)[3],
                )

        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0578_p2_frequency_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [17, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)

    def test_broader_04b9_authored_geometry(self):
        self.assertEqual(
            THIRTY_NINTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x04B9-p1-broader-frequency-reference",
        )
        self.assertEqual(
            len(build_twenty_second_authored_candidate_rgba()),
            256 * 256 * 4,
        )
        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_04b9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)

    def test_broader_0239_candidate_has_expected_envelope_and_contact(self):
        self.assertEqual(
            FORTIETH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0239-p1-broader-frequency-reference",
        )
        rgba = build_twenty_third_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0239_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)

    def test_broader_0439_candidate_has_expected_envelope_and_contact(self):
        self.assertEqual(
            FORTY_FIRST_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0439-p1-broader-frequency-reference",
        )
        rgba = build_twenty_fourth_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0439_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)

    def test_broader_0039_candidate_has_expected_envelope_and_contact(self):
        self.assertEqual(
            FORTY_SECOND_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0039-p1-broader-frequency-reference",
        )
        rgba = build_twenty_fifth_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0039_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)

    def test_broader_00b9_candidate_has_expected_envelope_and_contact(self):
        self.assertEqual(
            FORTY_THIRD_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x00B9-p1-broader-frequency-reference",
        )
        rgba = build_twenty_sixth_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_00b9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)

    def test_broader_02b9_candidate_has_expected_envelope_and_contact(self):
        self.assertEqual(
            FORTY_FOURTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x02B9-p1-broader-frequency-reference",
        )
        rgba = build_twenty_seventh_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_02b9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)

    def test_broader_01b9_candidate_has_expected_envelope_and_contact(self):
        self.assertEqual(
            FORTY_FIFTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x01B9-p1-broader-frequency-reference",
        )
        rgba = build_twenty_eighth_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_01b9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)

    def test_broader_0139_candidate_has_expected_envelope_and_contact(self):
        self.assertEqual(
            FORTY_SIXTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0139-p1-broader-frequency-reference",
        )
        rgba = build_twenty_ninth_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = [
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0139_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        ]
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)

    def test_broader_0539_candidate_has_expected_envelope_contact_and_delta(self):
        self.assertEqual(
            FORTY_SEVENTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0539-p1-broader-frequency-reference",
        )
        rgba = build_thirtieth_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0539_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        previous = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0139_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)
        self.assertEqual(occupied - previous, {(42, 28), (43, 28)})
        self.assertEqual(previous - occupied, set())

    def test_broader_05b9_candidate_has_expected_envelope_contact_and_delta(self):
        self.assertEqual(
            FORTY_EIGHTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x05B9-p1-broader-frequency-reference",
        )
        rgba = build_thirty_first_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_05b9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        previous = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0539_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)
        self.assertTrue(occupied != previous)
        self.assertTrue({(42, 29), (43, 29)} <= occupied)

    def test_broader_03b9_candidate_has_expected_envelope_contact_and_delta(self):
        self.assertEqual(
            FORTY_NINTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x03B9-p1-broader-frequency-reference",
        )
        rgba = build_thirty_second_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_03b9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        previous = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_05b9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)
        self.assertEqual(
            occupied - previous,
            {(38, 22), (39, 22), (39, 23), (40, 23)},
        )
        self.assertEqual(previous - occupied, set())

    def test_broader_0339_candidate_has_expected_envelope_contact_and_delta(self):
        self.assertEqual(
            FIFTIETH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0339-p1-broader-frequency-reference",
        )
        rgba = build_thirty_third_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0339_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        previous = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_03b9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)
        self.assertEqual(
            occupied - previous,
            {(41, 24), (41, 25), (41, 30), (41, 31),
             (42, 24), (42, 25), (42, 30), (42, 31), (43, 30)},
        )
        self.assertEqual(previous - occupied, set())

    def test_broader_0379_candidate_has_expected_envelope_contact_and_delta(self):
        self.assertEqual(
            FIFTY_FIRST_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0379-p1-broader-frequency-reference",
        )
        rgba = build_thirty_fourth_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0379_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        previous = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0339_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)
        self.assertEqual(
            occupied - previous,
            {(34, 29), (35, 29), (38, 31), (41, 23)},
        )
        self.assertEqual(previous - occupied, set())

    def test_broader_05f9_candidate_has_expected_envelope_contact_and_delta(self):
        self.assertEqual(
            FIFTY_SECOND_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x05F9-p1-broader-frequency-reference",
        )
        rgba = build_thirty_fifth_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_05f9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        previous = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0379_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)
        self.assertEqual(
            occupied - previous,
            {(37, 24), (38, 25), (38, 26), (36, 30),
             (37, 30), (38, 29), (38, 30)},
        )
        self.assertEqual(previous - occupied, set())

    def test_broader_p2_0546_0eb2_candidate_has_measured_envelope_contact(self):
        self.assertEqual(
            FIFTY_THIRD_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x0546-p2-companion-0EB2-broader-frequency-reference",
        )
        rgba = build_thirty_sixth_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_0546_p2_0eb2_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        self.assertEqual(len(occupied), 345)
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [17, 4, 41, 37],
        )
        bottom = [x for x, y in occupied if y == 37]
        self.assertEqual(min(bottom) + max(bottom), 51)

    def test_broader_03f9_candidate_has_expected_envelope_contact_and_delta(self):
        self.assertEqual(
            FIFTY_FOURTH_AUTHORED_REPRESENTATION_ID,
            "ordinary-racer-0x03F9-p1-broader-frequency-reference",
        )
        rgba = build_thirty_seventh_authored_candidate_rgba()
        self.assertEqual(len(rgba), 256 * 256 * 4)
        occupied = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_03f9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        previous = {
            (lx, ly)
            for ly in range(64)
            for lx in range(64)
            if sample_authored_05f9_p1_broader_rgba(
                lx * 4 + 2, ly * 4 + 2
            )[3] != 0
        }
        self.assertEqual(
            [
                min(x for x, _ in occupied),
                min(y for _, y in occupied),
                max(x for x, _ in occupied),
                max(y for _, y in occupied),
            ],
            [18, 5, 47, 36],
        )
        bottom = [x for x, y in occupied if y == 36]
        self.assertEqual(min(bottom) + max(bottom), 77)
        self.assertEqual(
            occupied - previous,
            {(39, 30), (39, 31), (39, 32)},
        )
        self.assertEqual(previous - occupied, set())

    def test_safe_name_is_path_stable(self):
        self.assertEqual(safe_name("racer / 0x0541:p1"), "racer-0x0541-p1")


if __name__ == "__main__":
    unittest.main()
