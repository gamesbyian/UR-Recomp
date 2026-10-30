"""ONE-03: P1 finish must freeze checkpoint splits before RESULTS."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"


def body(source, start, end):
    return source.split(start, 1)[1].split(end, 1)[0]


class One03FinishCaptureOrder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOST.read_text(encoding="utf-8")

    def test_p1_finish_is_observed_before_same_frame_checkpoint(self):
        after = body(
            self.source,
            'extern "C" void ur_uniracers_modern_after_run_frame(',
            'extern "C" int ur_uniracers_modern_settled_main_menu(',
        )
        capture = body(
            after,
            'if (run_active && g_run_capture.capturing()) {',
            '\n    }',
        )
        self.assertLess(
            capture.index('observe_run_finish_line();'),
            capture.index('observe_run_record_split();'),
        )

    def test_late_checkpoints_cannot_enter_p1_capture(self):
        split = body(
            self.source,
            'void observe_run_record_split() {',
            'void complete_multiplayer_run_record_capture() {',
        )
        self.assertIn(
            'if (!g_run_capture.capturing() || g_run_finish_ticks60) return;',
            split,
        )
        self.assertIn('g_run_capture.observe_split(', split)

    def test_failed_finish_split_is_not_silently_ignored(self):
        finalize = body(
            self.source,
            'void complete_run_record_capture() {',
            'void ',
        )
        self.assertIn('if (!g_run_capture.observe_split(', finalize)
        self.assertIn('UR_RUN_RECORD FINISH_SPLIT_REJECTED', finalize)
        self.assertIn('g_run_capture.abort_attempt();', finalize)
        self.assertIn('g_run_ghost_trace_capture.abort_attempt();', finalize)


if __name__ == '__main__':
    unittest.main()
