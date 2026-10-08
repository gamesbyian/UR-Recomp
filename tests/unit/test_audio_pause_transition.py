from pathlib import Path
import unittest

from tools.build_audio_pause_route import (
    CHECKPOINTS, POST_CHECKPOINT_FRAMES, pause_checkpoint_route,
)
from tools.check_native_audio_checkpoint_timing import validate_log
from tools.analyze_audio_pause_phases import pause_phase_report

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tests/input/ui-pause-route.script"


class GuestPauseAudioAcceptanceTests(unittest.TestCase):
    def test_derived_routes_preserve_canonical_start_press_count(self):
        source = SOURCE.read_text(encoding="utf-8")
        for case, presses in zip(CHECKPOINTS, (0, 1, 2)):
            with self.subTest(case=case):
                script = pause_checkpoint_route(source, case)
                self.assertEqual(script.count("press start 2"), presses)
                self.assertTrue(script.endswith(
                    f"dump {case}\nwait {POST_CHECKPOINT_FRAMES}\n"
                    f"dump {case}-audio-post\nquit\n"
                ))
                self.assertNotIn("poke ", script)
                self.assertIn("until 0313 == 01 1800", script)
                self.assertEqual(script.count("\nquit\n"), 1)
                observed = validate_log(
                    f"script f=1050 dump {case} ok\n"
                    f"script f=1080 dump {case}-audio-post ok\n", case)
                self.assertEqual(observed["guest_frames_after_checkpoint"], 30)

    def test_unexpected_route_changes_fail_closed(self):
        source = SOURCE.read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            pause_checkpoint_route(source, "not-a-checkpoint")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            pause_checkpoint_route(source + "\ndump ui-pause-before\n", "ui-pause-before")
        with self.assertRaisesRegex(ValueError, "Start presses"):
            pause_checkpoint_route(source.replace("press start 2", "wait 2", 1),
                                   "ui-pause-after-start")
        with self.assertRaisesRegex(ValueError, "may not quit/poke"):
            pause_checkpoint_route(source.replace("dump ui-pause-before", "poke 009F 01\ndump ui-pause-before"),
                                   "ui-pause-before")

    def fixtures(self):
        pcm, stats = {}, {}
        for case, rms in zip(CHECKPOINTS, (1500, 0, 1700)):
            pcm[case] = {
                "schema_version": 1, "audio_origin": "sdl3-disk-playback",
                "channels": 2, "device_format": "S16LE", "tail_duration_seconds": 1,
                "tail_rms": rms, "tail_channel_rms": [rms, rms],
                "tail_nonzero_fraction": (0 if rms == 0 else 0.95),
            }
            stats[case] = {
                "schema_version": 1, "audio_origin": "snesrecomp-production-audio-stats",
                "deltas": {"dropped_audible": 0, "underflows": 8, "missing_frames": 4000},
                "post_startup_deltas": {"dropped_audible": 0, "underflows": 0,
                                        "missing_frames": 0},
            }
        return pcm, stats

    def test_silent_pause_is_recorded_not_assumed_or_rejected(self):
        pcm, stats = self.fixtures()
        report = pause_phase_report(pcm, stats)
        self.assertEqual(report["phases"]["ui-pause-after-start"]["tail_rms"], 0)
        self.assertEqual(report["relative_to_before"]["ui-pause-after-start"], 0)
        self.assertIsNone(report["relative_to_before_db"]["ui-pause-after-start"])
        self.assertGreater(report["relative_to_before_db"]["ui-pause-after-resume"], 0)
        self.assertAlmostEqual(report["relative_to_before"]["ui-pause-after-resume"], 1700 / 1500, delta=1e-6)

    def test_opt_in_pause_attenuation_and_resume_recovery(self):
        pcm, stats = self.fixtures()
        report = pause_phase_report(
            pcm, stats, max_paused_to_before=0.05, min_resumed_to_before=0.5,
        )
        self.assertEqual(report["limits"]["max_paused_to_before"], 0.05)
        self.assertEqual(report["limits"]["min_resumed_to_before"], 0.5)
        pcm["ui-pause-after-start"]["tail_rms"] = 300
        with self.assertRaisesRegex(ValueError, "stock pause RMS ratio"):
            pause_phase_report(pcm, stats, max_paused_to_before=0.1)
        pcm, stats = self.fixtures()
        pcm["ui-pause-after-resume"]["tail_rms"] = 400
        with self.assertRaisesRegex(ValueError, "stock resume RMS ratio"):
            pause_phase_report(pcm, stats, min_resumed_to_before=0.5)

    def test_zero_pre_pause_baseline_never_vacuously_passes_opt_in_limit(self):
        pcm, stats = self.fixtures()
        pcm["ui-pause-before"]["tail_rms"] = 0
        report = pause_phase_report(pcm, stats)
        self.assertIsNone(report["relative_to_before"]["ui-pause-after-resume"])
        self.assertIsNone(report["relative_to_before_db"]["ui-pause-after-resume"])
        with self.assertRaisesRegex(ValueError, "without audible pre-pause"):
            pause_phase_report(pcm, stats, max_paused_to_before=0.05)

    def test_invalid_attenuation_limits_fail_closed(self):
        pcm, stats = self.fixtures()
        with self.assertRaisesRegex(ValueError, "non-negative finite"):
            pause_phase_report(pcm, stats, max_paused_to_before=float("nan"))
        with self.assertRaisesRegex(ValueError, "non-negative finite"):
            pause_phase_report(pcm, stats, min_resumed_to_before=-0.1)

    def test_windows_pause_acceptance_uses_measured_limits_only(self):
        workflow = (ROOT / ".github/workflows/windows-native-audio-output.yml").read_text()
        pause = workflow.split("      - name: Capture stock guest Start pause/resume audio envelopes", 1)[1]
        pause = pause.split("      - name: Upload bounded audio evidence", 1)[0]
        self.assertIn("--max-paused-to-before 0.05", pause)
        self.assertIn("--min-resumed-to-before 0.50", pause)
        self.assertIn("--max-new-audible-drops 0", pause)
        self.assertIn("--max-post-startup-underflows 0", pause)
        self.assertIn("--max-post-startup-missing-frames 0", pause)
        self.assertIn("--min-rms 0 --min-nonzero-fraction 0", pause)
        self.assertIn("tools/build_audio_pause_route.py", pause)
        self.assertNotIn("poke ", pause)

    def test_invalid_or_dropped_source_audio_rejected(self):
        pcm, stats = self.fixtures()
        stats["ui-pause-after-start"]["deltas"]["dropped_audible"] = 1
        with self.assertRaisesRegex(ValueError, "samples were lost"):
            pause_phase_report(pcm, stats)
        pcm, stats = self.fixtures()
        pcm["ui-pause-before"]["tail_channel_rms"] = [100, float("nan")]
        with self.assertRaisesRegex(ValueError, "invalid stereo"):
            pause_phase_report(pcm, stats)
        pcm, stats = self.fixtures()
        pcm["ui-pause-before"]["tail_duration_seconds"] = 0.5
        with self.assertRaisesRegex(ValueError, "one-second"):
            pause_phase_report(pcm, stats)
        pcm, stats = self.fixtures()
        del stats["ui-pause-after-resume"]
        with self.assertRaisesRegex(ValueError, "missing or extra"):
            pause_phase_report(pcm, stats)


if __name__ == "__main__":
    unittest.main()
