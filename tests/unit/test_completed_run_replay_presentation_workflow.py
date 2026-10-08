"""Keep the real-artifact alternate-presentation replay acceptance connected."""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/completed-run-replay-acceptance.yml"


class CompletedRunReplayPresentationWorkflowTests(unittest.TestCase):
    def test_captured_run_is_replayed_in_alternate_host_presentation(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        begin = workflow.index("- name: Re-drive identical saved run under alternate Modern presentation")
        end = workflow.index("- name: Launch stored run through Local Runs browser", begin)
        step = workflow[begin:end]
        self.assertIn("'UR-HOST-STATE/6'", step)
        for value in (
            "'widescreen=16x9'",
            "'internal_render_scale=1x'",
            "'vsync=off'",
            'SNESRECOMP_INPUT_FILE="$RUNNER_TEMP/rehydrated.input"',
            'UR_RUN_RECORD_CAPTURE_PATH="$ALTERNATE"',
            '"$RUNNER_TEMP/compare-runs" "$ORIGINAL" "$ALTERNATE"',
            '"$RUNNER_TEMP/compare-ghost-traces"',
            "UR_RUN_GHOST DRAWN",
        ):
            with self.subTest(value=value):
                self.assertIn(value, step)
        self.assertIn('grep -q "UR_RUN_GHOST_TRACE_COMPARE PASS', step)
        self.assertIn('grep -q "UR_RUN_REPLAY_COMPARE PASS', step)

    def test_original_host_state_is_written_by_bash(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        begin = workflow.index("- name: Capture completed Dragster run")
        end = workflow.index("- name: Rehydrate replay input from saved artifact", begin)
        capture = workflow[begin:end]
        start = capture.index("          printf ")
        finish = capture.index('          SDL_AUDIODRIVER=dummy', start)
        script = capture[start:finish]
        # Execute the shell formatting, catching broken continuation and
        # accidental literal backslash-n sequences that static greps miss.
        with tempfile.TemporaryDirectory() as tempdir:
            state = pathlib.Path(tempdir) / "host-state.txt"
            subprocess.run(
                ["bash", "-euo", "pipefail", "-c", 'STATE="$1"\\n' + script, "bash", str(state)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                state.read_text(encoding="utf-8").splitlines(),
                [
                    "UR-HOST-STATE/6", "profile=",
                    "regional_presentation=north_america",
                    "pause_on_focus_loss=1", "vibration_enabled=1",
                    "display_mode=windowed", "vsync=on",
                    "presentation_fps=game", "output_resolution=native",
                    "widescreen=original", "internal_render_scale=4x",
                ],
            )

    def test_original_control_loads_pinned_four_x_original_view(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        begin = workflow.index("- name: Capture completed Dragster run")
        end = workflow.index("- name: Rehydrate replay input from saved artifact", begin)
        capture = workflow[begin:end]
        for token in (
            "'vsync=on'",
            "'widescreen=original'",
            "'internal_render_scale=4x'",
            'UR_HOST_STATE_PATH="$STATE"',
            "UR_HOST_STATE LOADED",
        ):
            self.assertIn(token, capture)

    def test_real_profile_ghost_is_loaded_without_capture_overrides(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        begin = workflow.index(
            "- name: Render persisted Previous ghost through ordinary profile state")
        end = workflow.index("- name: Launch stored run through Local Runs browser", begin)
        step = workflow[begin:end]
        for expected in (
            "'profile=default'",
            "'UR-HOST-PROFILE/5'",
            "'ghost_target=previous'",
            'UR_RECOMP_USER_DATA_ROOT="$USER_ROOT"',
            'UR_PROFILE_SAVE_ROOT="$PROFILE_ROOT"',
            'UR_HOST_STATE_PATH="$STATE"',
            "UR_RUN_GHOSTS BOUND compatible=1",
            "UR_RUN_GHOST_TRACE PLAYBACK_BOUND target=previous",
            "UR_RUN_GHOST DRAWN",
            '"$RUNNER_TEMP/compare-runs" "$ORIGINAL" "$REPLAYED"',
            '"$RUNNER_TEMP/compare-ghost-traces"',
        ):
            self.assertIn(expected, step)
        self.assertNotIn("UR_RUN_GHOST_ACCEPTANCE_RECORD=", step)
        self.assertNotIn("UR_RUN_RECORD_CAPTURE_PATH=", step)

    def test_remains_manual_only(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        triggers = workflow.split("on:", 1)[1].split("concurrency:", 1)[0]
        self.assertIn("workflow_dispatch:", triggers)
        self.assertNotIn("pull_request:", triggers)
        self.assertNotIn("push:", triggers)


if __name__ == "__main__":
    unittest.main()
