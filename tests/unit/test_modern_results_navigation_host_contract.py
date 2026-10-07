import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
HARNESS = ROOT / "tests" / "native" / "run_modern_results_navigation_acceptance.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "modern-results-navigation-acceptance.yml"


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
            mapped.count("handle_results_navigation("), 3)
        self.assertIn("repeat_current_attempt()", source)

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
        self.assertNotIn("activate_results_navigation_action(", acceptance)

    def test_quick_practice_and_authentic_are_explicit_acceptance_cases(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        harness = HARNESS.read_text(encoding="utf-8")
        self.assertIn("UR_RESULTS_NAV_ACCEPTANCE=practice", harness)
        self.assertIn("UR_EXECUTION_MODE=authentic", harness)
        self.assertIn("next=0 track=0 tour=0 repeat=1", harness)
        self.assertIn("! grep -q \"UR_RESULTS_NAV MENU\"", harness)

    def test_dedicated_workflow_owns_native_route_acceptance(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run_modern_results_navigation_acceptance.sh", workflow)
        self.assertIn("test_modern_results_navigation_cpp", workflow)
        self.assertIn("test_modern_results_navigation_host_contract", workflow)
        self.assertNotIn("modern_pad_glyph", workflow)
        self.assertNotIn("racer_hd", workflow)


if __name__ == "__main__":
    unittest.main()
