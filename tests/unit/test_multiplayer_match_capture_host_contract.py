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
        self.assertIn("kOrdinaryTwoPlayerRaceResultMenu", source)
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
        frame_hook = source.index(
            'extern "C" void ur_uniracers_modern_after_run_frame'
        )
        multiplayer_live = source.index(
            "g_multiplayer_run_capture.capturing()", frame_hook
        )
        multiplayer_observe = source.index(
            "g_multiplayer_run_capture.observe_guest_frame(",
            multiplayer_live,
        )
        next_frame_arg = source.index(
            "stats->controller_word", multiplayer_observe
        )
        self.assertLess(multiplayer_live, multiplayer_observe)
        self.assertLess(multiplayer_observe, next_frame_arg)

        # Ordinary 2P result ownership is distinct from the generic Restart
        # classifier; completion must key off the validated 0xF9 authority.
        self.assertIn(
            "g_ram[0x009F] ==\n            ur::title::kOrdinaryTwoPlayerRaceResultMenu",
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
        quit_request = body.index("request_desktop_quit()", acceptance)
        completed = body.index(
            '"UR_MULTIPLAYER_MATCH ACCEPTANCE_COMPLETE"', quit_request
        )
        rejected = body.index(
            '"UR_MULTIPLAYER_MATCH ACCEPTANCE_QUIT_REJECTED"', completed
        )

        self.assertLess(store, captured)
        self.assertLess(captured, reset)
        self.assertLess(reset, acceptance)
        self.assertLess(acceptance, quit_request)
        self.assertLess(quit_request, completed)
        self.assertLess(completed, rejected)

        # Every terminal authority failure must retire the isolated 2P capture
        # instead of leaving it armed for stale profile/course/result context.
        for diagnostic in (
            "SESSION_IDENTITY_LOST",
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

    def test_unsettled_2p_result_keeps_capture_armed(self):
        source = (
            ROOT / "native" / "product" / "uniracers_modern_host.cpp"
        ).read_text(encoding="utf-8")
        complete = source.index("void complete_multiplayer_run_record_capture()")
        complete_end = source.index("void complete_run_record_capture()", complete)
        body = source[complete:complete_end]
        observed = body.index("if (!observed)")
        context = body.index("bind_local_multiplayer_match_context(", observed)
        transient = body[observed:context]
        self.assertIn("return;", transient)
        self.assertNotIn("reset_multiplayer_run_capture();", transient)
        self.assertNotIn("RESULT_REJECTED", transient)

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

    def test_records_acceptance_fixture_exercises_both_resolved_lanes(self):
        fixture = (
            ROOT / "tests" / "input" / "two-player-records-acceptance.input"
        ).read_text(encoding="utf-8")
        script = (
            ROOT / "tests" / "input" / "two-player-records-acceptance.script"
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
        self.assertTrue(any(p1 != 0 for _, _, p1, _ in race_rows))
        self.assertTrue(any(p2 != 0 for _, _, _, p2 in race_rows))
        self.assertIn((1518, 24, 0x081, 0x040), race_rows)
        self.assertIn("turbo on", script)
        self.assertIn("wait 50000", script)
        self.assertIn("dump records-acceptance-unresolved", script)
        self.assertNotIn("forcepoke", script)
        self.assertNotIn("poke ", script)

    def test_acceptance_uses_exact_process_local_profiles(self):
        source = (
            ROOT / "native" / "product" / "uniracers_modern_host.cpp"
        ).read_text(encoding="utf-8")
        begin = source.index("void maybe_run_multiplayer_match_acceptance()")
        end = source.index("void observe_regional_title_surface()", begin)
        body = source[begin:end]

        self.assertIn('{"accept-p1", {"MIKE", 0}}', body)
        self.assertIn('{"accept-p2", {"ANDREW", 1}}', body)
        self.assertNotIn("persist_profile_catalog(", body)
        self.assertNotIn("save_host_profile_catalog_file(", body)

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
