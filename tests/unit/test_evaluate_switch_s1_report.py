import tempfile
import unittest
from pathlib import Path

from tools.evaluate_switch_s1_report import evaluate, merge_reports, parse_report


def report_text(*, modes: str, styles: str, background: int, foreground: int) -> str:
    return f"""UR-SWITCH-S1/1
scope=hardware-observation-only
lifecycle_started=1
clean_exit=1
operation_mode=0
operation_modes_seen={modes}
display_ready=1
display_size=1280x720
audio_ready=1
storage_writable=1
input_seen=1
controller_styles_seen={styles}
background_events={background}
foreground_events={foreground}
suspend_resume_observed={int(background > 0 and foreground > 0)}
"""


class SwitchS1ReportEvaluatorTest(unittest.TestCase):
    def test_combined_hardware_sessions_can_close_s1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handheld = root / "handheld.txt"
            docked = root / "docked.txt"
            handheld.write_text(
                report_text(modes="0x1", styles="0x2", background=1, foreground=1)
            )
            docked.write_text(
                report_text(modes="0x2", styles="0x5", background=0, foreground=0)
            )
            result = evaluate(merge_reports([parse_report(handheld), parse_report(docked)]))
            self.assertTrue(result["passed"])

    def test_missing_pro_controller_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.txt"
            path.write_text(
                report_text(modes="0x3", styles="0x6", background=1, foreground=1)
            )
            result = evaluate(merge_reports([parse_report(path)]))
            self.assertFalse(result["passed"])
            self.assertFalse(result["checks"]["pro_controller_observed"])

    def test_hardware_failures_are_not_merged_away(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.txt"
            bad = Path(tmp) / "bad.txt"
            good.write_text(
                report_text(modes="0x1", styles="0x2", background=1, foreground=1)
            )
            bad_text = report_text(
                modes="0x2", styles="0x5", background=0, foreground=0
            ).replace("audio_ready=1", "audio_ready=0")
            bad.write_text(bad_text)
            result = evaluate(merge_reports([parse_report(good), parse_report(bad)]))
            self.assertFalse(result["passed"])
            self.assertFalse(result["checks"]["audio_ready"])


if __name__ == "__main__":
    unittest.main()
