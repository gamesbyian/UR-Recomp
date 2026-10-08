import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class PauseRestartResumesContractTests(unittest.TestCase):
    def test_pause_menu_restart_resumes_after_restore(self):
        source = HOST.read_text(encoding="utf-8")
        start = source.index("    if (selected == UR_MODERN_PAUSE_RESTART) {")
        body = source[start:source.index("    return dispatch(UR_MODERN_PAUSE_ACTIVATE);\n}", start)]
        restore = body.index("dispatch(UR_MODERN_PAUSE_ACTIVATE)")
        rearm = body.index("rearm_run_capture_after_retry();")
        resume = body.index("paused() && dispatch(UR_MODERN_PAUSE_TOGGLE)")
        # Resume only after a successful restore and capture re-arm.
        self.assertLess(restore, rearm)
        self.assertLess(rearm, resume)
        self.assertIn("if (handled) {", body)


if __name__ == "__main__":
    unittest.main()
