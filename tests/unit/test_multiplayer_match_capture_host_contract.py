import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class MultiplayerMatchCaptureHostContractTests(unittest.TestCase):
    def test_production_ordinary_2p_capture_is_separate_and_paired(self):
        source = (
            ROOT / "native" / "product" / "uniracers_modern_host.cpp"
        ).read_text(encoding="utf-8")

        self.assertIn("CompletedRunCapture g_multiplayer_run_capture", source)
        self.assertIn("RunRecordCaptureKind::OrdinaryTwoPlayerRace", source)
        self.assertIn("resolve_run_record_capture_plan(", source)
        self.assertIn('"multiplayer-runs"', source)
        self.assertIn("observe_ordinary_two_player_race_result(", source)
        self.assertIn("bind_local_multiplayer_match_context(", source)
        self.assertIn("append_multiplayer_match_pair(", source)
        self.assertIn("ordinary_two_player_carrier_elapsed_ticks60(", source)
        self.assertIn('"race-1p"', source)
        self.assertIn("CompletedRunCapture g_run_capture", source)

        # 2P capture must not inherit the 1P ghost/PB pipeline.
        begin = source.index("bool begin_multiplayer_run_record_capture(")
        end = source.index("void observe_run_ghost_trace_sample()", begin)
        body = source[begin:end]
        self.assertNotIn("refresh_run_ghosts(", body)
        self.assertNotIn("refresh_run_ghost_playback_trace(", body)
        self.assertNotIn("g_run_ghost_trace_capture", body)

        complete = source.index("void complete_multiplayer_run_record_capture()")
        complete_end = source.index("void complete_run_record_capture()", complete)
        completion_body = source[complete:complete_end]
        self.assertNotIn("ur_uniracers_run_data_ticks60", completion_body)
        self.assertNotIn('observe_split("finish"', completion_body)

        # The resolved framework controller word is the common replay carrier.
        self.assertIn(
            "g_multiplayer_run_capture.observe_guest_frame(\n"
            "                stats->controller_word)",
            source,
        )

        # A dropped live participant session invalidates the in-flight match.
        self.assertIn(
            '"UR_MULTIPLAYER_MATCH ABORTED_IDENTITY_LOST"', source
        )

    def test_generated_product_build_registers_multiplayer_authority(self):
        patcher = (
            ROOT / "tools" / "patch_modern_product_host.py"
        ).read_text(encoding="utf-8")

        for name in (
            "local_multiplayer_participants.cpp",
            "local_multiplayer_match_binding.cpp",
            "multiplayer_match_record.cpp",
            "uniracers_two_player_result.cpp",
        ):
            self.assertIn(name, patcher)


if __name__ == "__main__":
    unittest.main()
