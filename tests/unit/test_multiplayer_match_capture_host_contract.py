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

    def test_acceptance_quits_only_after_successful_pair_persistence(self):
        source = (
            ROOT / "native" / "product" / "uniracers_modern_host.cpp"
        ).read_text(encoding="utf-8")

        complete = source.index("void complete_multiplayer_run_record_capture()")
        complete_end = source.index("void complete_run_record_capture()", complete)
        body = source[complete:complete_end]

        store = body.index("append_multiplayer_match_pair(")
        captured = body.index('"UR_MULTIPLAYER_MATCH CAPTURED')
        reset = body.index("reset_multiplayer_run_capture();", captured)
        acceptance = body.index(
            'if (std::getenv("UR_MULTIPLAYER_MATCH_ACCEPTANCE"))',
            reset,
        )
        completed = body.index(
            '"UR_MULTIPLAYER_MATCH ACCEPTANCE_COMPLETE"', acceptance
        )
        quit_request = body.index("request_desktop_quit();", completed)

        self.assertLess(store, captured)
        self.assertLess(captured, reset)
        self.assertLess(reset, acceptance)
        self.assertLess(acceptance, completed)
        self.assertLess(completed, quit_request)

        # Every terminal authority failure must retire the isolated 2P capture
        # instead of leaving it armed for stale profile/course/result context.
        for diagnostic in (
            "SESSION_IDENTITY_LOST",
            "RESULT_REJECTED",
            "PARTICIPANT_BIND_REJECTED",
            "FINALIZE_REJECTED",
            "METADATA_REJECTED",
            "STORE_FAILED",
        ):
            marker = body.index(diagnostic)
            following_reset = body.index(
                "reset_multiplayer_run_capture();", marker
            )
            self.assertLess(marker, following_reset)

    def test_live_capture_rejects_lost_participant_context(self):
        source = (
            ROOT / "native" / "product" / "uniracers_modern_host.cpp"
        ).read_text(encoding="utf-8")

        frame_hook = source.index(
            'extern "C" void ur_uniracers_modern_after_run_frame'
        )
        live = source.index(
            "g_multiplayer_run_capture.capturing()", frame_hook
        )
        lost = source.index(
            '"UR_MULTIPLAYER_MATCH ABORTED_IDENTITY_LOST"', live
        )
        reset = source.index("reset_multiplayer_run_capture();", lost)
        observe = source.index(
            "g_multiplayer_run_capture.observe_guest_frame(", reset
        )
        self.assertLess(live, lost)
        self.assertLess(lost, reset)
        self.assertLess(reset, observe)

    def test_active_capture_revalidates_captured_course_and_profiles(self):
        source = (
            ROOT / "native" / "product" / "uniracers_modern_host.cpp"
        ).read_text(encoding="utf-8")
        frame_hook = source.index(
            'extern "C" void ur_uniracers_modern_after_run_frame'
        )
        live = source.index(
            "g_multiplayer_run_capture.capturing()", frame_hook
        )
        observe = source.index(
            "g_multiplayer_run_capture.observe_guest_frame(", live
        )
        body = source[live:observe]

        self.assertIn("if (run_active)", body)
        self.assertIn("ur_uniracers_identify_course(", body)
        self.assertIn("current_course.course_index ==", body)
        self.assertIn("*g_local_multiplayer_participants.player1 ==", body)
        self.assertIn("*g_local_multiplayer_participants.player2 ==", body)
        self.assertIn('"UR_MULTIPLAYER_MATCH STALE_SESSION_CONTEXT"', body)
        active_guard = body.index("if (run_active)")
        course_read = body.index("ur_uniracers_identify_course(", active_guard)
        stale = body.index('"UR_MULTIPLAYER_MATCH STALE_SESSION_CONTEXT"')
        reset = body.index("reset_multiplayer_run_capture();", stale)
        self.assertLess(active_guard, course_read)
        self.assertLess(course_read, stale)
        self.assertLess(stale, reset)

    def test_both_finish_fixture_mirrors_p2_horizontal_drive(self):
        fixture = (
            ROOT / "tests" / "input" / "two-player-both-finish.input"
        ).read_text(encoding="utf-8")

        race_rows = []
        for raw in fixture.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            start, duration, p1, p2 = line.split(":")
            if int(start) < 1194:
                continue
            race_rows.append(
                (int(start), int(duration), int(p1, 16), int(p2, 16))
            )

        self.assertTrue(race_rows)
        for start, duration, p1, p2 in race_rows:
            self.assertGreater(duration, 0, msg=f"frame {start}")
            self.assertEqual(p1 & 0x080, 0x080, msg=f"frame {start}")
            self.assertEqual(p2 & 0x040, 0x040, msg=f"frame {start}")
            self.assertEqual(p1 & 0x001, p2 & 0x001, msg=f"frame {start}")
            self.assertEqual(p1 & 0x040, 0, msg=f"frame {start}")
            self.assertEqual(p2 & 0x080, 0, msg=f"frame {start}")

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
