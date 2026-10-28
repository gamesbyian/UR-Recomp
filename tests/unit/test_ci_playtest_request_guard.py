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
        new = (marker(1, "Investigate merged RF083 word-entry and RF084 native writer on Zoo")
               + "- Observer mode: **on**\n")
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

    def test_zoo_observer_mode_is_explicit_unique_and_fail_closed(self):
        old = marker(12, "Original and native echo returned values were measured")
        for mode, enabled in (("on", True), ("off", False)):
            current = (marker(13, "Measure same-source observer noninterference control")
                       + f"- Observer mode: **{mode}**\n")
            verdict = guard.validate(old, current, [guard.ZOO_MARKER],
                                     marker=guard.ZOO_MARKER)
            self.assertIs(verdict["observer_enabled"], enabled)
        for suffix in (
            "",
            "- Observer mode: **disabled**\n",
            "- Observer mode: **ON**\n",
            "- Observer mode: **on**\n- Observer mode: **off**\n",
            "- Observer mode: **off**\n- Observer mode: **off**\n",
            "- Observer mode: **off**\n- Observer mode: **INVALID**\n",
        ):
            with self.subTest(suffix=suffix):
                with self.assertRaisesRegex(ValueError, "observer mode"):
                    guard.validate(old,
                                   marker(13, "Measure same-source observer noninterference control") + suffix,
                                   [guard.ZOO_MARKER], marker=guard.ZOO_MARKER)

    def test_rf094_sequence20_explicit_mode_is_unique_and_paired(self):
        old = (marker(19, "Original CPU SPC case completed at Bowl boundary")
               + "- Observer mode: **on**\n")
        base = marker(20, "Observe DSP register writes and the late F7 response stream")
        for mode, expected in (("on", True), ("off", False)):
            current = (base + "- Observer mode: **on**\n"
                       + f"- RF094 DSP follow-through: **{mode}**\n")
            verdict = guard.validate(old, current, [guard.ZOO_MARKER],
                                     marker=guard.ZOO_MARKER)
            self.assertTrue(verdict["observer_enabled"])
            self.assertIs(verdict["rf094_enabled"], expected)
        malformed = (
            base + "- Observer mode: **on**\n",
            base + "- Observer mode: **on**\n- RF094 DSP follow-through: **ON**\n",
            base + "- Observer mode: **on**\n- RF094 DSP follow-through: on\n",
            base + "- Observer mode: **on**\n- RF094 DSP follow-through: **on**\n"
                   + "- RF094 DSP follow-through: **off**\n",
            base + "- Observer mode: **on**\n- RF094 DSP follow-through: **off**\n"
                   + "- RF094 DSP follow-through: **off**\n",
            base + "- Observer mode: **off**\n- RF094 DSP follow-through: **on**\n",
        )
        for current in malformed:
            with self.subTest(current=current[-100:]), self.assertRaisesRegex(
                    ValueError, "RF094"):
                guard.validate(old, current, [guard.ZOO_MARKER],
                               marker=guard.ZOO_MARKER)

    def test_earlier_zoo_request_cannot_inherit_rf094(self):
        old = marker(18, "The previous real SPC echo experiment completed")
        now = (marker(19, "Observe next Bowl original CPU and SPC edges")
               + "- Observer mode: **on**\n")
        verdict = guard.validate(old, now, [guard.ZOO_MARKER],
                                 marker=guard.ZOO_MARKER)
        self.assertTrue(verdict["observer_enabled"])
        self.assertFalse(verdict["rf094_enabled"])

    def test_rf094_on_reaches_real_guard_gha_output(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            previous = Path(tmp) / "previous.md"
            current = Path(tmp) / "current.md"
            output = Path(tmp) / "gha-output.txt"
            previous.write_text(
                marker(19, "Last real native and original F7 port case completed")
                + "- Observer mode: **on**\n", encoding="utf-8")
            current.write_text(
                marker(20, "Observe post DSP commits and the late F7 payloads")
                + "- Observer mode: **on**\n"
                + "- RF094 DSP follow-through: **on**\n", encoding="utf-8")
            with (mock.patch.object(sys, "argv", [
                "ci_playtest_request_guard.py", "--previous", str(previous),
                "--current", str(current), "--source-sha", "b" * 40,
                "--marker", guard.ZOO_MARKER, "--gha-output", str(output)]),
                  mock.patch.object(guard, "changed_files",
                                    return_value=[guard.ZOO_MARKER])):
                self.assertEqual(guard.main(), 0)
            self.assertEqual(output.read_text(encoding="utf-8"),
                             "observer_enabled=true\nrf094_enabled=true\n")

    def test_zoo_cli_writes_validated_mode_to_job_output(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            previous = Path(tmp) / "previous.md"
            current = Path(tmp) / "current.md"
            output = Path(tmp) / "gha-output.txt"
            previous.write_text(marker(12, "Prior source-matched paired echo case"), encoding="utf-8")
            current.write_text(
                marker(13, "Run one original/native observer-off control case")
                + "- Observer mode: **off**\n", encoding="utf-8")
            with (mock.patch.object(sys, "argv", [
                "ci_playtest_request_guard.py", "--previous", str(previous),
                "--current", str(current), "--source-sha", "a" * 40,
                "--marker", guard.ZOO_MARKER, "--gha-output", str(output)]),
                  mock.patch.object(guard, "changed_files", return_value=[guard.ZOO_MARKER])):
                self.assertEqual(guard.main(), 0)
            self.assertEqual(output.read_text(encoding="utf-8"),
                             "observer_enabled=false\nrf094_enabled=false\n")

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
                         "zoo_dp_window: true",
                         "source_followthrough: true", "zoo_next_bowl: true",
                         "qa01_cold_guest_reload: true",
                         "baldosa_refresh_beam_rate: true",
                         "baldosa_io_clock_order: true"):
            self.assertIn(required, text)
        # These three opt-ins must travel together on the exact same Zoo case:
        # authentic result follow-through, genuine next-event progression and
        # independent fresh-guest earned SRAM reload. Never enable a broad
        # all-case campaign or a second unguarded producer.
        self.assertEqual(text.count("source_followthrough: true"), 1)
        self.assertEqual(text.count("zoo_next_bowl: true"), 1)
        self.assertEqual(text.count("qa01_cold_guest_reload: true"), 1)
        owning = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text(
            encoding="utf-8")
        for declared in ("source_followthrough:", "zoo_next_bowl:",
                         "qa01_cold_guest_reload:"):
            self.assertIn(declared, owning)
        self.assertIn('row.get("disposition") not in ("strict_candidate", "strict_divergence")', owning)
        self.assertIn('row.get("release_credit") != 0', owning)
        # A real strict divergence may still carry source-earned cold-guest
        # evidence, but no release admission is made by this wrapper.
        self.assertIn('"$producer_rc" -eq 0 || "$producer_rc" -eq 1', owning)
        # Both original and native observers are disabled together for control.
        expression = "${{ needs.qualify_request.outputs.observer_enabled == 'true' }}"
        self.assertIn("observer_enabled: ${{ steps.guard.outputs.observer_enabled }}", text)
        self.assertIn("rf094_enabled: ${{ steps.guard.outputs.rf094_enabled }}", text)
        self.assertIn("qa01_rf094_spc_dsp: ${{ needs.qualify_request.outputs.rf094_enabled == 'true' }}", text)
        self.assertIn("id: guard", text)
        self.assertIn('--gha-output "$GITHUB_OUTPUT"', text)
        self.assertIn("qa01_rf084_native_sound_dp: " + expression, text)
        self.assertIn("qa01_rf088_rf089_echo: " + expression, text)
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
