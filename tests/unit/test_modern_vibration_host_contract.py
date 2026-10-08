import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
HARNESS = ROOT / "tests" / "native" / "run_modern_vibration_acceptance.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "modern-onboarding-practice-acceptance.yml"
ONBOARDING_PATHS = ROOT / ".github" / "ci" / "modern-native-onboarding-paths.txt"


def _body(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


class ModernVibrationHostContractTests(unittest.TestCase):
    def test_pulses_come_only_from_policy_and_authoritative_events(self):
        source = HOST.read_text(encoding="utf-8")
        emitter = _body(source, "void emit_haptic_event(", "void observe_run_finish_line() {")
        self.assertIn("ur::product::haptic_pulse_for(", emitter)
        self.assertIn("g_product_state.settings", emitter)
        self.assertIn("g_run_timing_supported && g_run_capture.capturing()", emitter)
        for forbidden in ("g_ram[", "RtlTryWriteSram", "g_sram"):
            self.assertNotIn(forbidden, emitter)
        split = _body(source, "void observe_run_record_split() {", "void complete_run_record_capture() {")
        self.assertEqual(split.count("emit_haptic_event("), 1)
        self.assertIn("emit_haptic_event(ur::product::HapticEvent::Checkpoint);", split)
        # The finish pulse fires on the line-crossing frame (the official
        # finish), not seconds later when RESULTS completes the record.
        finish = _body(source, "void observe_run_finish_line() {", "void observe_run_record_split() {")
        self.assertEqual(finish.count("emit_haptic_event("), 1)
        self.assertIn("emit_haptic_event(ur::product::HapticEvent::Finish);", finish)
        completion = _body(source, "void complete_run_record_capture() {", "const auto record =")
        self.assertNotIn("emit_haptic_event(", completion)
        self.assertEqual(source.count("emit_haptic_event(ur::product::HapticEvent::"), 2)

    def test_options_row_persists_through_product_state(self):
        source = HOST.read_text(encoding="utf-8")
        toggle = _body(source, "bool toggle_vibration_setting() {", "bool step_volume_setting(")
        self.assertIn("if (!modern_mode()) return false;", toggle)
        self.assertIn("persist_product_state(candidate)", toggle)
        persist = toggle.index("persist_product_state(candidate)")
        commit = toggle.index("g_product_state = candidate;")
        self.assertLess(persist, commit)
        self.assertIn("case UR_MODERN_OPTIONS_VIBRATION:\n        return toggle_vibration_setting();", source)

    def test_native_acceptance_is_wired(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        harness = HARNESS.read_text(encoding="utf-8")
        for marker in (
            "UR_VIBRATION SELECTED enabled=0",
            "'^vibration_enabled=0$'",
            "vibration changed the authoritative race outcome",
            '! grep -q "UR_HAPTIC PULSE" "$WORK/off.log"',
            '! grep -q "UR_HAPTIC PULSE" "$WORK/authentic.log"',
        ):
            self.assertIn(marker, harness)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        paths = ONBOARDING_PATHS.read_text(encoding="utf-8")
        self.assertIn("run_modern_vibration_acceptance.sh", workflow)
        self.assertIn("native/product/haptic_feedback_policy.hpp", paths)


if __name__ == "__main__":
    unittest.main()
