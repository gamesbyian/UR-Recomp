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


class RacerHdLiveDrawCensusTests(unittest.TestCase):
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

    def test_armed_but_declined_output_counts_actual_original(self):
        result = analyze("\n".join([
            gate(70, "armed", "full-pair"),
            present(70, "original", "unsupported-output"),
        ]))["measurement"]
        self.assertEqual(result["capture_armed_guest_frames"], 1)
        self.assertEqual(result["armed_without_hd_draw_guest_frames"], 1)
        self.assertEqual(result["hd_presented_fraction"], 0)
        self.assertEqual(result["stock_fallback_fraction"], 1)

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
             "mixed HD and Original"),
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

    def test_episode_rejects_duplicate_frame_ids(self):
        self.assertEqual(episode_lengths([1, 2, 4, 8, 9]), [2, 1, 2])
        with self.assertRaisesRegex(ValueError, "unique"):
            episode_lengths([1, 1])


if __name__ == "__main__":
    unittest.main()
