import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
HARNESS = ROOT / "tests" / "native" / "run_modern_next_event_acceptance.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "modern-onboarding-practice-acceptance.yml"
ONBOARDING_PATHS = ROOT / ".github" / "ci" / "modern-native-onboarding-paths.txt"


def _body(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    return source[start:source.index(end_marker, start)]


class ModernNextEventHostContractTests(unittest.TestCase):
    def test_next_event_reuses_resume_restore_before_selection(self):
        source = HOST.read_text(encoding="utf-8")
        apply = source.index("const auto applied = ur::title::apply_tour_resume(")
        enter = source.index("enter_modern_tour_next_event_selection(", apply)
        selecting = source.index('"UR_NEXT_EVENT SELECTING', enter)
        self.assertLess(apply, enter)
        self.assertLess(enter, selecting)

    def test_race_entry_never_rolls_back_progression(self):
        source = HOST.read_text(encoding="utf-8")
        body = _body(
            source,
            "void advance_tour_continue_route(uint64_t next_frame) {",
            "bool retire_tour_continuation_after_stock_reset() {",
        )
        entered = body.index("if (step.next_event_race_entered) {")
        unexpected = body.index("ABORTED_UNEXPECTED_RACE")
        self.assertLess(entered, unexpected)
        block = body[entered:unexpected]
        self.assertIn('cancel_tour_continue("UR_NEXT_EVENT RACE_ENTERED")', block)
        self.assertNotIn("abort_tour_continue", block)
        self.assertNotIn("rollback", block)

    def test_route_target_comes_from_unique_derivation_only(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index(
            "bool begin_tour_entry(ur::product::ModernTourEntryIntent intent) {"
        )
        # Bound the production route by its own closing brace, not an
        # unrelated later handler. Adjacent Practice modal functions have
        # a separate read-only stock SRAM availability contract.
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        self.assertIn("ur::product::unique_next_track_id(", body)
        self.assertIn("ur::product::begin_modern_tour_next_event(", body)
        for forbidden in ("g_ram[0x009B] =", "g_sram[", "RtlTryWriteSram"):
            self.assertNotIn(forbidden, body)

    def test_acceptance_uses_frame_boundary_keyboard_handler(self):
        source = HOST.read_text(encoding="utf-8")
        body = _body(
            source,
            "void run_next_event_acceptance() {",
            'extern "C" void ur_uniracers_modern_after_run_frame(',
        )
        self.assertIn("ur_uniracers_modern_system_key_down(SDLK_F3, 0, 0)", body)
        self.assertNotIn("begin_tour_entry(", body)

    def test_harness_and_workflow_cover_hidden_routed_and_cancelled(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        harness = HARNESS.read_text(encoding="utf-8")
        self.assertIn("run_case ambiguous 11000 inspect", harness)
        self.assertIn("run_case next-event 11110 confirm", harness)
        self.assertIn("run_case cancel 11110 cancel", harness)
        self.assertIn("RACE_VERIFIED expected=4 actual=4 course_equal=1", harness)
        self.assertNotIn("xdotool", harness)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        paths = ONBOARDING_PATHS.read_text(encoding="utf-8")
        self.assertIn("run_modern_next_event_acceptance.sh", workflow)
        self.assertIn("tests/native/run_modern_next_event_acceptance.sh", paths)
        self.assertIn("tests/input/modern-tour-next-event-acceptance.script", paths)


if __name__ == "__main__":
    unittest.main()
