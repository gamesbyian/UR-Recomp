import unittest

from tools.measure_racer_hd_live_draws import analyze, episode_lengths


def gate(frame, status, reason):
    return (
        f"UR_RACER_HD_CENSUS frame={frame} phase=gate "
        f"status={status} reason={reason}"
    )


def present(frame, status, reason):
    return (
        f"UR_RACER_HD_CENSUS frame={frame} phase=present "
        f"status={status} reason={reason}"
    )


def pixel_change(frame, sources, changed):
    return (
        f"UR_RACER_HD_PIXEL_CHANGE frame={frame} "
        f"source_instances={sources} changed_from_underlay={changed}"
    )


class RacerHdLiveDrawCensusTests(unittest.TestCase):
    def test_native_hd_callback_is_not_necessarily_a_visible_pixel_change(self):
        log = "\n".join([
            gate(1139, "armed", "full-pair"),
            pixel_change(1139, 0, 0),
            present(1139, "hd", "full-pair"),
            gate(1140, "original", "overlapping-source-obj"),
            present(1140, "original", "not-armed"),
            gate(1141, "armed", "p1-only"),
            pixel_change(1141, 1, 1),
            present(1141, "hd", "p1-only"),
            gate(1142, "armed", "full-pair"),
            pixel_change(1142, 2, 0),
            present(1142, "hd", "full-pair"),
        ])
        result = analyze(log)["measurement"]
        self.assertEqual(result["hd_drawn_guest_frames"], 3)
        self.assertEqual(result["hd_pixel_change_witness_guest_frames"], 3)
        self.assertEqual(result["hd_with_source_footprint_guest_frames"], 2)
        self.assertEqual(result["hd_with_actual_changed_pixels_guest_frames"], 1)
        self.assertEqual(result["hd_without_actual_changed_pixels_guest_frames"], 2)
        self.assertEqual(result["hd_actual_changed_guest_frame_ids"], [1141])
        result = analyze(log, from_frame=1140, to_frame=1142)["measurement"]
        self.assertEqual(result["hd_with_actual_changed_pixels_guest_frames"], 1)
        self.assertEqual(result["hd_pixel_change_witness_guest_frames"], 2)
        # A guest frame may be presented twice. Count its changed-output
        # outcome once, but require one witness per actual render call.
        repeated = analyze("\n".join([
            gate(90, "armed", "p1-only"),
            pixel_change(90, 1, 0),
            present(90, "hd", "p1-only"),
            pixel_change(90, 1, 1),
            present(90, "hd", "p1-only"),
        ]))["measurement"]
        self.assertEqual(repeated["hd_pixel_change_witness_guest_frames"], 1)
        self.assertEqual(repeated["hd_with_actual_changed_pixels_guest_frames"], 1)

    def test_pixel_change_witness_fails_closed(self):
        bad = [
            ([gate(1, "armed", "full-pair"), pixel_change(1, 0, 1),
              present(1, "hd", "full-pair")], "source-absent"),
            ([gate(1, "armed", "full-pair"), pixel_change(1, 1, 1),
              pixel_change(1, 1, 1), present(1, "hd", "full-pair")],
             "pixel-change witness count"),
            ([gate(1, "armed", "full-pair"),
              "UR_RACER_HD_PIXEL_CHANGE frame=1 source_instances=5 changed_from_underlay=1",
              present(1, "hd", "full-pair")], "malformed pixel-change"),
            ([gate(1, "original", "disabled"), pixel_change(1, 1, 1),
              present(1, "original", "not-armed")],
             "pixel-change witness missing or on non-HD"),
            ([gate(1, "armed", "full-pair"), pixel_change(1, 1, 1),
              present(1, "hd", "full-pair"),
              gate(2, "armed", "full-pair"), present(2, "hd", "full-pair")],
             "pixel-change witness missing or on non-HD"),
        ]
        for lines, reason in bad:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(ValueError, reason):
                    analyze("\n".join(lines))

    def test_actual_present_outcomes_and_temporal_edges(self):
        log = "\n".join([
            gate(10, "original", "p1-selection-or-art"),
            present(10, "original", "not-armed"),
            gate(11, "armed", "full-pair"),
            present(11, "hd", "full-pair"),
            present(11, "hd", "full-pair"),  # repeat present, not new guest frame
            gate(12, "armed", "full-pair"),
            present(12, "hd", "full-pair"),
            gate(13, "armed", "p1-only"),
            present(13, "hd", "p1-only"),
            gate(14, "original", "p2-pair-gate"),
            present(14, "original", "not-armed"),
            gate(16, "original", "unsupported-geometry"),
            present(16, "original", "not-armed"),
            gate(18, "armed", "full-pair"),  # never presented
        ])
        report = analyze(log)["measurement"]
        self.assertEqual(report["guest_frames_observed"], 7)
        self.assertEqual(report["guest_frames_with_host_presents"], 6)
        self.assertEqual(report["host_present_calls"], 7)
        self.assertEqual(report["hd_present_calls"], 4)
        self.assertEqual(report["hd_drawn_guest_frames"], 3)
        self.assertEqual(report["original_presented_guest_frames"], 3)
        self.assertEqual(report["hd_drawn_player_frames"], 5)
        self.assertEqual(report["player_frame_denominator"], 12)
        self.assertEqual(report["hd_player_frame_fraction"], 5 / 12)
        self.assertEqual(report["hd_presented_fraction"], .5)
        self.assertEqual(report["stock_fallback_fraction"], .5)
        self.assertEqual(report["hd_run_lengths"], [3])
        self.assertEqual(report["one_frame_hd_runs"], 0)
        self.assertEqual(report["draw_mode_switches"], 2)
        self.assertEqual(report["original_to_hd_edges"], 1)
        self.assertEqual(report["hd_to_original_edges"], 1)
        self.assertEqual(report["consecutive_presented_guest_frame_pairs"], 4)
        self.assertEqual(report["armed_without_hd_draw_guest_frame_ids"], [18])
        self.assertEqual(report["nonpresented_guest_frame_ids"], [18])
        self.assertEqual(report["gate_fallback_reasons"], {
            "p1-selection-or-art": 1,
            "p2-pair-gate": 1,
            "unsupported-geometry": 1,
        })

    def test_sparse_baldosa_guest_and_host_frame_denominators(self):
        # The PPU can take a destructive source-OBJ decision on a guest
        # frame even if the SDL host never requests presentation there.
        # No host present is missing evidence, not a black/missing rider.
        events = [gate(frame, "original", "overlapping-source-obj")
                  for frame in range(1850, 1924)]
        events += [
            present(1856, "original", "not-armed"),
            present(1872, "original", "not-armed"),
            present(1900, "original", "not-armed"),
            gate(1924, "armed", "full-pair"),  # guest not presented
            gate(1925, "armed", "full-pair"),
            pixel_change(1925, 1, 1),
            present(1925, "hd", "full-pair"),
            pixel_change(1925, 1, 0),
            present(1925, "hd", "full-pair"),
        ]
        m = analyze("\n".join(events))["measurement"]
        self.assertEqual(m["guest_frames_observed"], 76)
        self.assertEqual(m["guest_frames_with_host_presents"], 4)
        self.assertEqual(m["guest_frames_without_host_presents"], 72)
        self.assertEqual(m["host_present_calls"], 5)
        self.assertEqual(m["guest_frames_with_host_presents_fraction"], 4 / 76)
        self.assertEqual(m["armed_without_host_present_guest_frames"], 1)
        self.assertEqual(m["armed_without_host_present_guest_frame_ids"], [1924])
        self.assertEqual(m["armed_without_hd_draw_guest_frame_ids"], [1924])
        self.assertEqual(m["armed_with_hd_host_present_guest_frames"], 1)
        self.assertEqual(m["armed_with_original_host_present_guest_frames"], 0)
        self.assertEqual(m["overlap_refused_guest_frames"], 74)
        self.assertEqual(m["overlap_refused_with_host_present_guest_frames"], 3)
        self.assertEqual(m["overlap_refused_without_host_present_guest_frames"], 71)
        self.assertEqual(m["overlap_refused_stock_host_present_calls"], 3)
        self.assertEqual(m["hd_with_actual_changed_pixels_guest_frames"], 1)
        self.assertEqual(m["hd_present_calls"], 2)
        self.assertEqual(m["consecutive_presented_guest_frame_pairs"], 0)
        self.assertEqual(m["draw_mode_switches"], 0)
        # Do not transform guest-level original fallbacks into invented
        # 74 actual stock host presentations.
        with self.assertRaisesRegex(ValueError, "stock OBJ may have been removed"):
            analyze("\n".join(events + [
                present(1924, "original", "unsupported-output"),
            ]))

    def test_armed_but_declined_output_is_a_possible_missing_racer(self):
        with self.assertRaisesRegex(ValueError, "stock OBJ may have been removed"):
            analyze("\n".join([
                gate(70, "armed", "full-pair"),
                present(70, "original", "unsupported-output"),
            ]))

    def test_gaps_are_not_fake_transitions(self):
        result = analyze("\n".join([
            gate(10, "original", "disabled"),
            present(10, "original", "not-armed"),
            gate(13, "armed", "full-pair"),
            present(13, "hd", "full-pair"),
        ]))["measurement"]
        self.assertEqual(result["consecutive_presented_guest_frame_pairs"], 0)
        self.assertEqual(result["draw_mode_switches"], 0)
        self.assertEqual(result["one_frame_hd_runs"], 1)

    def test_legacy_transition_only_logs_are_not_counted(self):
        with self.assertRaisesRegex(ValueError, "no native Racer HD per-frame"):
            analyze(
                "UR_RACER_HD_DRAW PASS frame=1220 semantic=0541 viewport=top slot=98"
            )

    def test_error_conditions_reject_inconsistent_native_data(self):
        invalid = [
            ([gate(3, "original", "disabled"), present(3, "hd", "full-pair")],
             "HD draw after Original"),
            ([gate(3, "armed", "full-pair"), present(3, "hd", "p1-only")],
             "mode disagreement"),
            ([gate(3, "armed", "full-pair"), gate(3, "armed", "full-pair"),
              present(3, "hd", "full-pair")], "duplicate gate"),
            ([gate(3, "armed", "full-pair"), present(4, "hd", "full-pair")],
             "unobserved guest frame"),
            ([gate(3, "armed", "full-pair"), present(3, "hd", "full-pair"),
              present(3, "original", "unsupported-output")],
             "stock OBJ may have been removed"),
            ([gate(3, "armed", "unknown"), present(3, "hd", "full-pair")],
             "invalid armed capture mode"),
            ([gate(3, "armed", "full-pair"), present(3, "hd", "unknown")],
             "invalid HD render mode"),
            ([gate(3, "armed", "full-pair"), present(3, "unrecognized", "what")],
             "invalid present status"),
        ]
        for lines, message in invalid:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    analyze("\n".join(lines))

    def test_absent_present_or_gate_does_not_create_fake_measurement(self):
        with self.assertRaisesRegex(ValueError, "no native Racer HD per-present"):
            analyze(gate(1, "original", "disabled"))
        with self.assertRaisesRegex(ValueError, "no native Racer HD per-frame"):
            analyze(present(1, "original", "not-armed"))

    def test_exact_scoped_window_separates_race_from_boot(self):
        log = "\n".join([
            gate(1, "original", "disabled"),
            present(1, "original", "not-armed"),
            gate(2, "original", "disabled"),
            present(2, "original", "not-armed"),
            gate(3, "armed", "full-pair"),
            present(3, "hd", "full-pair"),
            gate(4, "armed", "full-pair"),
            present(4, "hd", "full-pair"),
            gate(5, "original", "p2-pair-gate"),
            present(5, "original", "not-armed"),
        ])
        whole = analyze(log)["measurement"]
        self.assertEqual(whole["hd_drawn_guest_frames"], 2)
        self.assertEqual(whole["guest_frames_with_host_presents"], 5)
        race = analyze(log, from_frame=3, to_frame=5)
        self.assertEqual(race["frame_window"], {
            "from": 3, "to": 5, "exact_gate_coverage": True
        })
        self.assertEqual(race["measurement"]["guest_frames_observed"], 3)
        self.assertEqual(race["measurement"]["hd_drawn_guest_frames"], 2)
        self.assertEqual(race["measurement"]["hd_presented_fraction"], 2 / 3)
        self.assertEqual(race["measurement"]["hd_run_lengths"], [2])
        self.assertEqual(race["measurement"]["draw_mode_switches"], 1)

    def test_window_rejects_missing_guest_frame_and_partial_bounds(self):
        log = "\n".join([
            gate(10, "armed", "full-pair"),
            present(10, "hd", "full-pair"),
            gate(12, "original", "p2-pair-gate"),
            present(12, "original", "not-armed"),
        ])
        with self.assertRaisesRegex(ValueError, "first missing frame 11"):
            analyze(log, from_frame=10, to_frame=12)
        with self.assertRaisesRegex(ValueError, "supplied together"):
            analyze(log, from_frame=10)
        with self.assertRaisesRegex(ValueError, "invalid inclusive"):
            analyze(log, from_frame=14, to_frame=10)

    def test_episode_rejects_duplicate_frame_ids(self):
        self.assertEqual(episode_lengths([1, 2, 4, 8, 9]), [2, 1, 2])
        with self.assertRaisesRegex(ValueError, "unique"):
            episode_lengths([1, 1])


if __name__ == "__main__":
    unittest.main()
