import unittest
from pathlib import Path

from tools.capture_exit_frontend_audio import verify_exit_log

ROOT = Path(__file__).resolve().parents[2]


class ExitFrontendAudioTests(unittest.TestCase):
    LOG = (
        "script f=1041 dump race-entered ok\n"
        "UR_EXIT_FRONTEND REQUESTED source=1 sram=CAFE1248 practice=0\n"
        "UR_EXIT_FRONTEND ACCEPTANCE_TRIGGER surface=1 pause=1 exit=1\n"
        "UR_EXIT_FRONTEND FRONTEND_READY menu=D7 sram=CAFE1248\n"
        "script f=1180 dump audio-returned-main ok\n"
        "UR_EXIT_FRONTEND FRONTEND_USABLE menu=3C sram=CAFE1248\n"
        "script f=1305 dump audio-returned-rider ok\n"
    )

    def test_authoritative_return_has_distinct_guest_race_and_frontend(self):
        result = verify_exit_log(self.LOG)
        self.assertEqual(result["race_entered_guest_frame"], 1041)
        self.assertEqual(result["frontend_rider_guest_frame"], 1305)
        self.assertEqual(result["authoritative_exit_requested"], 1)
        self.assertEqual(result["frontend_usable"], 1)

    def test_missing_duplicate_or_reversed_product_state_fails(self):
        for bad in (
            self.LOG.replace("UR_EXIT_FRONTEND REQUESTED ", "NOT_EXITED "),
            self.LOG + "UR_EXIT_FRONTEND FRONTEND_USABLE menu=3C sram=12345678\n",
            self.LOG.replace("FRONTEND_READY menu=D7", "FRONTEND_READY menu=3C"),
            self.LOG.replace("ACCEPTANCE_TRIGGER surface=1", "ACCEPTANCE_TRIGGER surface=2"),
            self.LOG.replace("script f=1305 dump audio-returned-rider ok\n", ""),
            self.LOG.replace("script f=1041", "script f=1500"),
            self.LOG.replace(
                "UR_EXIT_FRONTEND FRONTEND_READY menu=D7 sram=CAFE1248\n",
                "UR_EXIT_FRONTEND FRONTEND_READY menu=D7 sram=CAFE1248\n"
                "UR_EXIT_FRONTEND RESET_REQUEST_FAILED\n"
            ),
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                verify_exit_log(bad)

    def test_cannot_substitute_guest_or_harness_only_for_frontend_return(self):
        # Requiring both host product diagnostic and 0xD7->0x3C frontend
        # script proves that 1P race PCM cannot masquerade as menu playback.
        for remove in (
            "UR_EXIT_FRONTEND REQUESTED source=1 sram=CAFE1248 practice=0\n",
            "UR_EXIT_FRONTEND FRONTEND_USABLE menu=3C sram=CAFE1248\n",
            "script f=1180 dump audio-returned-main ok\n",
        ):
            with self.subTest(remove=remove), self.assertRaises(ValueError):
                verify_exit_log(self.LOG.replace(remove, ""))

    def test_audio_route_is_canonical_gameplay_then_unmodified_frontend_input(self):
        baseline = (ROOT / "tests/input/modern-focus-pause.script").read_text()
        route = (ROOT / "tests/input/audio-exit-frontend.script").read_text()
        self.assertTrue(baseline.endswith("wait 3600\n"))
        self.assertTrue(route.startswith(baseline[:-len("wait 3600\n")]))
        self.assertIn("until 009F == D7 2400", route)
        self.assertIn("until 009F == 3C 1200", route)
        self.assertIn("dump audio-returned-rider", route)
        self.assertNotIn("poke ", route)

    def test_native_supervisor_only_observes_production_host_and_sdl(self):
        tool = (ROOT / "tools/capture_exit_frontend_audio.py").read_text()
        self.assertIn("UR_EXIT_FRONTEND FRONTEND_USABLE", tool)
        self.assertIn("analyze(", tool)
        self.assertIn("_stop_entire_tree", tool)
        self.assertIn("min_tail_channel_rms=50", tool)
        self.assertNotIn("RtlReset(", tool)


if __name__ == "__main__":
    unittest.main()
