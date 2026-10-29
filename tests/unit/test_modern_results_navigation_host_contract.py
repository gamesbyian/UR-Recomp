import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
HARNESS = ROOT / "tests" / "native" / "run_modern_results_navigation_acceptance.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "modern-shared-native-acceptance.yml"


def _body(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    return source[start:source.index(end_marker, start)]


class ModernResultsNavigationHostContractTests(unittest.TestCase):
    def test_tour_results_require_latched_one_player_route(self):
        source = HOST.read_text(encoding="utf-8")
        body = _body(
            source,
            "std::optional<ur::title::TourProgress> current_results_tour_progress()",
            "bool results_navigation_router_available()",
        )
        self.assertIn("HostRacePresentationMode::OnePlayer", body)
        self.assertIn("g_practice_active", body)
        self.assertIn("UR_UNIRACERS_RESTART_RESULTS", body)

    def test_progression_routes_use_existing_reboot_and_tour_transport(self):
        source = HOST.read_text(encoding="utf-8")
        activate = _body(
            source,
            "bool activate_results_navigation_action(",
            "bool handle_results_navigation(",
        )
        pending = _body(
            source,
            "bool begin_pending_results_navigation_route()",
            "bool activate_results_navigation_action(",
        )
        self.assertIn("request_frontend_reboot(true)", activate)
        self.assertIn("begin_tour_entry(", pending)
        self.assertIn("ModernTourEntryIntent::NextEvent", pending)
        self.assertIn("begin_modern_tour_results_route(", pending)
        for body in (activate, pending):
            self.assertNotIn("g_ram[0x009B] =", body)
            self.assertNotIn("g_ram[0x009F] =", body)
            self.assertNotIn("g_sram[", body)

    def test_tour_select_reuses_existing_profile_snapshot_rollback(self):
        source = HOST.read_text(encoding="utf-8")
        route = _body(
            source,
            "void advance_tour_continue_route(uint64_t next_frame) {",
            "bool retire_tour_continuation_after_stock_reset() {",
        )
        ready = route.index("if (step.tour_select_ready")
        entered = route.index("if (step.next_event_race_entered)")
        self.assertLess(ready, entered)
        block = route[ready:entered]
        self.assertIn("rollback_tour_entry_to_profile_snapshot()", block)
        self.assertIn("UR_RESULTS_NAV TOUR_SELECT_READY", block)

    def test_track_select_reuses_resume_restore_before_release(self):
        source = HOST.read_text(encoding="utf-8")
        reconcile = _body(
            source,
            "void reconcile_tour_resume() {",
            "bool restart_surface() {",
        )
        apply = reconcile.index("const auto applied = ur::title::apply_tour_resume(")
        ready = reconcile.index("UR_RESULTS_NAV TRACK_SELECT_READY", apply)
        self.assertLess(apply, ready)

    def test_keyboard_and_mapped_controller_share_results_handler(self):
        source = HOST.read_text(encoding="utf-8")
        keyboard = _body(
            source,
            'extern "C" int ur_uniracers_modern_system_key_down(',
            'extern "C" int ur_uniracers_modern_system_gamepad_button(',
        )
        mapped = _body(
            source,
            'extern "C" int ur_uniracers_modern_system_gamepad_control(',
            'extern "C" uint32_t ur_uniracers_modern_filter_player_input(',
        )
        self.assertGreaterEqual(
            keyboard.count("handle_results_navigation("), 3)
        self.assertGreaterEqual(
            mapped.count("handle_results_navigation("), 2)
        # Confirm is the fixed host A button on the raw pad path.
        raw = _body(
            source,
            'extern "C" int ur_uniracers_modern_system_gamepad_button(',
            'extern "C" int ur_uniracers_modern_system_gamepad_control(',
        )
        self.assertIn(
            "handle_results_navigation(UR_MODERN_HOST_NAV_CONFIRM)", raw)
        self.assertIn("repeat_current_attempt()", source)

    def test_keyboard_and_physical_pad_repeat_shortcuts_share_guarded_route(self):
        # This is a source-bound routing contract, not physical-pad evidence.
        # Both one-button shortcuts must use the same target-validated
        # transaction as the results-menu Confirm action.
        source = HOST.read_text(encoding="utf-8")
        keyboard = _body(
            source,
            'extern "C" int ur_uniracers_modern_system_key_down(',
            'extern "C" int ur_uniracers_modern_controls_active(',
        )
        raw_pad = _body(
            source,
            'extern "C" int ur_uniracers_modern_system_gamepad_button(',
            'extern "C" int ur_uniracers_modern_system_gamepad_control(',
        )
        raw_results = _body(
            raw_pad,
            "if (results_navigation_active()) {",
            "if (g_frontend_options_active && g_options_visible) {",
        )
        self.assertIn("if (!pressed) return 1;", raw_results)
        self.assertIn(
            "if (button == kGamepadBtn_X) {\n"
            "            (void)repeat_current_attempt();",
            raw_results,
        )
        self.assertIn(
            "handle_results_navigation(UR_MODERN_HOST_NAV_CONFIRM)",
            raw_results,
        )
        self.assertNotIn("begin_practice(", raw_results)
        self.assertNotIn("UR_MODERN_PAUSE_RESTART_HOTKEY", raw_results)

        key_repeat = _body(
            keyboard,
            "if (modern_mode() && key == SDLK_r && (mod & KMOD_CTRL)",
            "return 0;\n}",
        )
        self.assertIn("g_surface == UR_UNIRACERS_RESTART_RESULTS", key_repeat)
        self.assertEqual(key_repeat.count("(void)repeat_current_attempt();"), 2)
        self.assertNotIn("begin_practice(", key_repeat)
        self.assertNotIn("UR_MODERN_PAUSE_RESTART_HOTKEY", key_repeat)

        guarded = _body(
            source,
            "bool repeat_current_attempt() {",
            "bool launch_recent_course_practice() {",
        )
        practice = guarded[:guarded.index("const uint32_t sram_before")]
        self.assertIn("begin_quick_practice_rematch_route(", practice)
        self.assertIn("REPEAT_PRACTICE_REJECTED_TARGET", practice)
        self.assertIn("request_frontend_reboot(true)", practice)
        self.assertNotIn("dispatch(UR_MODERN_PAUSE_RESTART_HOTKEY)", practice)

    def test_acceptance_enters_through_real_keyboard_handler(self):
        source = HOST.read_text(encoding="utf-8")
        acceptance = _body(
            source,
            "void run_results_navigation_acceptance() {",
            'extern "C" void ur_uniracers_modern_after_run_frame(',
        )
        self.assertIn(
            "ur_uniracers_modern_system_key_down(SDLK_DOWN, 0, 0)",
            acceptance,
        )
        self.assertIn(
            "ur_uniracers_modern_system_key_down(SDLK_RETURN, 0, 0)",
            acceptance,
        )
        self.assertIn("!g_next_event_verify_track", acceptance)
        self.assertNotIn("activate_results_navigation_action(", acceptance)


    def test_opt_in_second_race_and_cold_process_never_accept_route_only(self):
        source = HOST.read_text(encoding="utf-8")
        acceptance = _body(
            source, "void run_results_navigation_acceptance() {",
            'extern "C" void ur_uniracers_modern_after_run_frame(')
        self.assertIn('std::strcmp(mode, "next-earned") == 0', acceptance)
        self.assertIn('std::strcmp(mode, "next-earned-movie") == 0', acceptance)
        self.assertIn("snesrecomp_desktop_load_relative_input_file(source)", acceptance)
        self.assertIn("NEXT_MOVIE_SOURCE_INPUT_BOUND", acceptance)
        self.assertIn("g_results_navigation_acceptance_stage = 2;", acceptance)
        self.assertIn("g_run_finish_ticks60.has_value()", acceptance)
        self.assertIn("g_results_navigation_acceptance_first_sram", acceptance)
        self.assertIn("g_profile_state->autosave_generation >", acceptance)
        self.assertIn("NEXT_EARNED_RESULT observed=1", acceptance)
        harness = HARNESS.read_text(encoding="utf-8")
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        self.assertIn('run_case next-earned 01111 next-earned "$EARNED_SCRIPT"', harness)
        self.assertIn("NEXT_EARNED_COLD_REOPEN=source_second_result=1", harness)
        self.assertIn("if second_raw == first_raw:", harness)
        self.assertIn("if cold_raw != after_cold:", harness)
        self.assertIn('fields["stock_sram"]', harness)
        self.assertIn("if not source_earned_tour_awarded(first_raw, second_raw):", harness)
        self.assertIn("next-earned-pre-cold.srm", harness)
        self.assertIn("UR_ONE03_USE_2014_SOURCE_INPUT", harness)
        self.assertIn("--first-movie-frame 794 --frames 2080", harness)
        self.assertIn("dragster-2014-relative.input", harness)
        script = (ROOT / "tests/input/modern-results-next-earned.script").read_text()
        self.assertGreaterEqual(script.count("until 009F == 99"), 2)
        self.assertIn("dump next-event-race-results", script)
        self.assertIn("until 0313 == 01 3600", script)
        self.assertFalse(any(line.lstrip().startswith("poke ") for line in script.splitlines()))
        cold = (ROOT / "tests/input/modern-results-cold-reopen.script").read_text()
        self.assertIn("dump cold-main-menu", cold)
        movie = (ROOT / "tests/input/modern-results-next-earned-original-movie.script").read_text()
        self.assertIn("until 0313 == 01 3600", movie)
        self.assertIn("until 009F == 99 4800", movie)
        self.assertTrue(all(not line.startswith("press ")
                            for line in movie.split("dump race-results", 1)[1].splitlines()))

    def test_earned_tour_award_requires_real_win_and_completed_clear(self):
        # Execute the same Python predicate embedded in the acceptance
        # heredoc, rather than a second approximation of its conditions.
        import ast
        harness = HARNESS.read_text(encoding="utf-8")
        marker = "def source_earned_tour_awarded(first_raw, second_raw):"
        self.assertIn(marker, harness)
        body = _body(harness, marker, "if not source_earned_tour_awarded(")
        parsed = ast.parse(body)
        self.assertEqual(len(parsed.body), 1)
        namespace = {}
        exec(compile(ast.Module(body=parsed.body, type_ignores=[]),
                     str(HARNESS), "exec"), namespace)
        check = namespace["source_earned_tour_awarded"]

        def sram(row, medal, p1=2508, cpu=2798):
            raw = bytearray(8192)
            raw[0x1075:0x107A] = bytes(row)
            raw[0x069C] = medal
            raw[0x0769:0x076B] = p1.to_bytes(2, "little")
            raw[0x07D3:0x07D5] = cpu.to_bytes(2, "little")
            return bytes(raw)

        first = sram([0, 1, 1, 1, 1], 0, p1=2856)
        self.assertTrue(check(first, sram([0, 0, 0, 0, 0], 1)))
        # A malformed fifth byte, a medal without the source-mandated
        # row clear, and a fifth flag without award are not completed tours.
        self.assertFalse(check(first, sram([2, 1, 1, 1, 1], 0)))
        self.assertFalse(check(first, sram([0, 1, 1, 1, 1], 1)))
        self.assertFalse(check(first, sram([1, 1, 1, 1, 1], 0)))
        # Even a plausible cleared row and new medal cannot certify a loss.
        self.assertFalse(check(first, sram([0, 0, 0, 0, 0], 1, p1=2856)))
        self.assertFalse(check(first, sram([0, 0, 0, 0, 0], 0)))


    def test_earned_cold_reopen_executes_full_post_award_block(self):
        # A valid award previously passed the inner predicate but raised
        # NameError on function-local final_row/final_medal in the outer scope.
        import sys
        import tempfile

        harness = HARNESS.read_text(encoding="utf-8")
        marker = '"$COLD_DUMPS/cold-main-menu.sram.bin"'
        newline = chr(10)
        start_marker = "<<'PY'" + newline
        start = harness.index(start_marker, harness.index(marker)) + len(start_marker)
        script = harness[start:harness.index(newline + "PY" + newline, start)]
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            paths = [root / name for name in (
                "first.bin", "second.bin", "pre-save.srm", "pre-profile.txt",
                "post-save.srm", "post-profile.txt", "cold.bin")]
            first = bytearray(8192)
            first[0x1075:0x107A] = bytes((0, 1, 1, 1, 1))
            second = bytearray(first)
            second[0x1075:0x107A] = bytes(5)
            second[0x069C] = 1
            second[0x0769:0x076B] = (2508).to_bytes(2, "little")
            second[0x07D3:0x07D5] = (2798).to_bytes(2, "little")
            paths[0].write_bytes(first)
            for index in (1, 2, 4, 6):
                paths[index].write_bytes(second)
            for index in (3, 5):
                paths[index].write_text("stock_sram=" + second.hex() + newline)
            command = [sys.executable, "-c", script, *map(str, paths)]
            valid = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertIn("NEXT_EARNED_COLD_REOPEN=source_second_result=1", valid.stdout)
            # The first process continues for 180 frames after the
            # RESULTS dump. Its post-save typed profile and disk image must
            # agree at shutdown; unrelated bytes may change in that epoch.
            pre_exit = bytearray(second)
            pre_exit[0x10AD] ^= 1
            paths[2].write_bytes(pre_exit)
            paths[3].write_text("stock_sram=" + pre_exit.hex() + newline)
            pre_transient = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(pre_transient.returncode, 0, pre_transient.stderr)
            self.assertIn("result_to_exit_changed_offsets=10AD", pre_transient.stdout)
            # Reject a stale typed snapshot even when its original RESULTS
            # bytes happen to match the earlier dump.
            paths[3].write_text("stock_sram=" + second.hex() + newline)
            pre_stale = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(pre_stale.returncode, 0)
            self.assertIn("pre-cold typed SRAM/save mismatch", pre_stale.stderr)
            paths[3].write_text("stock_sram=" + pre_exit.hex() + newline)
            # Reject a lost medal before reboot, even if the pre-cold typed
            # profile and on-disk save are mutually consistent.
            pre_lost = bytearray(pre_exit)
            pre_lost[0x069C] = 0
            paths[2].write_bytes(pre_lost)
            paths[3].write_text("stock_sram=" + pre_lost.hex() + newline)
            pre_rejected = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(pre_rejected.returncode, 0)
            self.assertIn("second-result tour/medal not persisted", pre_rejected.stderr)
            paths[2].write_bytes(pre_exit)
            paths[3].write_text("stock_sram=" + pre_exit.hex() + newline)
            # A fresh boot may also change unrelated bytes. The cold typed
            # profile, saved file and guest dump must match their own epoch.
            cold = bytearray(pre_exit)
            cold[0x0050] ^= 1
            for index in (4, 6):
                paths[index].write_bytes(cold)
            paths[5].write_text("stock_sram=" + cold.hex() + newline)
            transient = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(transient.returncode, 0, transient.stderr)
            self.assertIn("progression_persisted=1", transient.stdout)
            # A stale typed profile cannot masquerade as an atomic cold save.
            paths[5].write_text("stock_sram=" + second.hex() + newline)
            stale = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("typed SRAM/save mismatch", stale.stderr)
            # Even with a consistent cold profile, losing the earned medal
            # must fail the independent progression-preservation check.
            changed = bytearray(cold)
            changed[0x069C] = 0
            paths[4].write_bytes(changed)
            paths[6].write_bytes(changed)
            paths[5].write_text("stock_sram=" + changed.hex() + newline)
            rejected = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("tour/medal not preserved", rejected.stderr)

    def test_2014_dragster_movie_source_exports_real_relative_controller_masks(self):
        # Actual archived source controller bytes, not a synthetic winning
        # race or a verified tour flag. The runtime test remains opt-in.
        import hashlib
        import json
        import sys
        import tempfile
        movie = ROOT / "reference/imported/tas-bots/dessyreqt-4250-submission.smv"
        self.assertEqual(
            hashlib.sha256(movie.read_bytes()).hexdigest(),
            "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442")
        with tempfile.TemporaryDirectory() as d:
            input_path = pathlib.Path(d) / "original-relative.input"
            report_path = pathlib.Path(d) / "source.json"
            subprocess.run([
                sys.executable, str(ROOT / "tools/extract_historical_smv_scene_window.py"),
                "--movie", str(movie), "--meta",
                str(ROOT / "analysis/generated/historical-2014-smv-metadata.json"),
                "--first-movie-frame", "794", "--frames", "2080",
                "--race-entry-frame", "0",
                "--input-out", str(input_path),
                "--json-out", str(report_path),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["movie_frame_range"], [794, 2873])
            self.assertEqual(report["frames"], 2080)
            # Independently observed original RESULTS starts at 2874;
            # never include the original post-result menu presses at 2894+.
            self.assertLess(report["movie_frame_range"][1], 2874)
            self.assertGreater(len(report["relative_input_segments"]), 0)
            self.assertGreater(input_path.stat().st_size, 0)
            self.assertFalse(any(line.startswith("poke ") for line in
                                 input_path.read_text().splitlines()))

    def test_repeat_rejects_stale_practice_identity_before_guest_restart(self):
        source = HOST.read_text(encoding="utf-8")
        repeat = _body(
            source,
            "bool repeat_current_attempt() {",
            "bool launch_recent_course_practice() {",
        )
        guard = repeat.index("begin_quick_practice_rematch_route(")
        reject = repeat.index("REPEAT_PRACTICE_REJECTED_TARGET")
        restart = repeat.index("dispatch(UR_MODERN_PAUSE_RESTART_HOTKEY)")
        self.assertLess(guard, reject)
        self.assertLess(reject, restart)
        self.assertIn("if (g_practice_active)", repeat)
        self.assertIn("g_recent_course_track_id", repeat)
        context = _body(
            source,
            "current_results_navigation_context() {",
            "void refresh_results_navigation_menu() {",
        )
        self.assertIn("quick_practice_repeat_target_ready(", context)
        self.assertIn("g_practice_launch", context)

    def test_repeat_practice_uses_stock_router_after_transactional_reboot(self):
        source = HOST.read_text(encoding="utf-8")
        repeat = _body(
            source,
            "bool repeat_current_attempt() {",
            "bool launch_recent_course_practice() {",
        )
        practice = repeat[:repeat.index("const uint32_t sram_before")]
        self.assertIn("begin_quick_practice_rematch_route(", practice)
        self.assertIn("request_frontend_reboot(true)", practice)
        self.assertIn("g_practice_rematch_route = rematch", practice)
        self.assertLess(
            practice.index("request_frontend_reboot(true)"),
            practice.index("g_practice_rematch_route = rematch"),
        )
        self.assertNotIn("dispatch(UR_MODERN_PAUSE_RESTART_HOTKEY)", practice)
        after_frame = _body(
            source,
            'extern "C" void ur_uniracers_modern_after_run_frame(',
            'extern "C" int ur_uniracers_modern_settled_main_menu(',
        )
        self.assertIn("advance_quick_practice_rematch_route(", after_frame)
        self.assertIn("begin_practice(step.track_id)", after_frame)
        self.assertIn("REPEAT_PRACTICE_ROUTER_TIMEOUT", after_frame)
        self.assertIn("REPEAT_PRACTICE_ROUTER_FAILED", after_frame)
        self.assertIn("REPEAT_PRACTICE_ROUTER_RACE_READY", source)

    def test_quick_practice_and_authentic_are_explicit_acceptance_cases(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        harness = HARNESS.read_text(encoding="utf-8")
        self.assertIn("UR_RESULTS_NAV_ACCEPTANCE=practice", harness)
        self.assertIn("UR_EXECUTION_MODE=authentic", harness)
        self.assertIn("next=0 track=0 tour=0 repeat=1", harness)
        self.assertIn('assert_absent_grep -q "UR_RESULTS_NAV MENU"', harness)

    def test_negative_diagnostics_fail_closed_without_changing_patterns(self):
        harness = HARNESS.read_text(encoding="utf-8")
        self.assertNotIn("! grep -q", harness)
        self.assertEqual(harness.count("assert_absent_grep -q "), 11)
        self.assertIn('if grep "$@"; then', harness)
        self.assertIn('if [ "$grep_status" -ne 1 ]; then', harness)

    def test_shared_workflow_owns_sharded_native_route_acceptance(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run_modern_results_navigation_acceptance.sh", workflow)
        self.assertIn("shard: [selection, progression, isolation]", workflow)
        self.assertIn("test_modern_results_navigation_cpp", workflow)
        self.assertIn("test_modern_results_navigation_host_contract", workflow)
        self.assertNotIn("modern_pad_glyph", workflow)
        self.assertNotIn("racer_hd", workflow)


if __name__ == "__main__":
    unittest.main()
