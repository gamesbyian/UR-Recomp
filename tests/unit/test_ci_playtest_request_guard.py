"""No accidental PR or unrelated merge may launch costly Windows packaging."""
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import ci_playtest_request_guard as guard


def marker(sequence, reason="Generate the first integrated-main verified ROM-free Windows candidate"):
    return ("# Windows playtest request\n\n"
            f"- Request sequence: **{sequence}** (used)\n"
            f"- Requested reason: {reason}\n")


class PlaytestRequestGuardTests(unittest.TestCase):
    def test_only_one_new_single_file_request_is_accepted(self):
        result = guard.validate(
            marker(1, "Earlier verified candidate is already available"),
            marker(2, "New native source changed after real product bug was repaired"),
            [guard.MARKER])
        self.assertEqual(result["old"], 1)
        self.assertEqual(result["new"], 2)
        self.assertEqual(result["release_gate_credit"], 0)

    def test_refuse_same_decrement_jump_empty_duplicate_or_false_reason(self):
        previous = marker(1, "Previous legitimate verified native candidate")
        for current in (
            marker(1, "Next legitimate candidate but same sequence"),
            marker(0, "Next legitimate candidate but decreasing sequence"),
            marker(3, "Next legitimate candidate but jumping sequence"),
            marker(2, "short"),
            marker(2, "Previous legitimate verified native candidate"),
            marker(2, "Initial dispatch contract installation; nothing requested"),
            marker(2) + "- Request sequence: **4**\n",
            marker(2).replace("- Requested reason: ", "- Misspelled reason: "),
            marker("02"),
        ):
            with self.subTest(current=current[-110:]):
                with self.assertRaises(ValueError):
                    guard.validate(previous, current, [guard.MARKER])

    def test_refuse_extra_changed_sources_and_renamed_marker(self):
        prev = marker(1, "Original release candidate held for testing")
        now = marker(2, "New native source requires exact new executable build")
        for paths in (
            [], ["docs/WORK-QUEUE.md", guard.MARKER],
            [guard.MARKER, "native/product/session_control.cpp"],
            [guard.MARKER, guard.MARKER],
            ["docs/playtest/renamed-playtest-marker.md"],
        ):
            with self.subTest(paths=paths):
                with self.assertRaisesRegex(ValueError, "change only"):
                    guard.validate(prev, now, paths)

    def test_git_diff_uses_exact_commit_and_parent(self):
        sha = "a" * 40
        with mock.patch.object(guard.subprocess, "check_output",
                               return_value=(guard.MARKER + "\0").encode()) as proc:
            self.assertEqual(guard.changed_files(sha), [guard.MARKER])
        cmd = proc.call_args.args[0]
        self.assertEqual(cmd[-2:], [sha + "^", sha])
        self.assertIn("--no-renames", cmd)
        with self.assertRaisesRegex(ValueError, "40-hex"):
            guard.changed_files("main")

    def test_original_native_zoo_request_reuses_strict_source_isolation(self):
        old = marker(0, "Initial causal dispatch marker installation without a run")
        new = marker(1, "Investigate merged RF083 word-entry and RF084 native writer on Zoo")
        self.assertEqual(
            guard.validate(old, new, [guard.ZOO_MARKER],
                           marker=guard.ZOO_MARKER)["new"], 1)
        with self.assertRaisesRegex(ValueError, "supported request marker"):
            guard.validate(old, new,
                           [guard.ZOO_MARKER, "native/product/race.cpp"],
                           marker=guard.ZOO_MARKER)
        with self.assertRaisesRegex(ValueError, "supported request marker"):
            guard.validate(old, new, [guard.ZOO_MARKER],
                           marker="docs/anything-else.md")

    def test_zoo_wrapper_requires_guard_then_calls_existing_causal_campaign(self):
        path = ROOT / ".github/workflows/qa01-zoo-causal-request.yml"
        text = path.read_text(encoding="utf-8")
        self.assertIn("    branches: [main]", text)
        self.assertIn('      - "docs/qa01/REQUEST-ZOO-CAUSAL.md"', text)
        self.assertNotIn("  pull_request:", text)
        self.assertIn("needs: qualify_request", text)
        self.assertIn("needs.qualify_request.result == 'success'", text)
        self.assertIn("uses: ./.github/workflows/qa01-event-campaign.yml", text)
        for required in ("selected: zoom-zoo", "zoo_race_mesh: true",
                         "zoo_dp_window: true", "qa01_rf084_native_sound_dp: true",
                         "baldosa_refresh_beam_rate: true",
                         "baldosa_io_clock_order: true"):
            self.assertIn(required, text)
        # Explicitly exclude unsafe experimental correction mixing,
        # event acceptance and publication.
        for unwanted in ("baldosa_spc_reference_rate: true",
                         "baldosa_dp_pointer_once: true",
                         "baldosa_hdma_cpu_stall: true",
                         "qa01_apu_phase: true", "contents: write"):
            self.assertNotIn(unwanted, text)

    def test_workflow_runs_guard_before_expensive_reusable_bridge(self):
        source = (ROOT / ".github/workflows/manual-romfree-windows-playtest.yml"
                  ).read_text(encoding="utf-8")
        self.assertIn("  qualify_request:", source)
        self.assertIn("fetch-depth: 2", source)
        self.assertIn("tools/ci_playtest_request_guard.py", source)
        self.assertIn("needs: qualify_request", source)
        self.assertIn("needs.qualify_request.result == 'success'", source)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.mode == 'publish_provisional_preview'", source)
        self.assertIn('      - "docs/playtest/REQUEST-WINDOWS-PLAYTEST.md"', source)
        self.assertNotIn("  pull_request:", source)


if __name__ == "__main__":
    unittest.main()
