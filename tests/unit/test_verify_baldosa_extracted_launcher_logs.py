#!/usr/bin/env python3
"""Retained extracted-CMD transcripts are bounded and the artifact is separate."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_baldosa_windows_extracted_launcher as verifier


class RetainedLauncherTranscriptTests(unittest.TestCase):
    def test_small_logs_are_kept_verbatim_and_large_ones_bounded(self):
        self.assertEqual(verifier.bounded_log("a\nb\n"), "a\nb\n")
        big = "H" * (1 << 20) + "MIDDLE" * 100000 + "T" * (1 << 20)
        out = verifier.bounded_log(big)
        self.assertLess(len(out.encode()), verifier.LOG_RETAIN_LIMIT + 200)
        self.assertTrue(out.startswith("H") and out.endswith("T"))
        self.assertIn("bytes elided by the verifier's bounded retention", out)

    def test_every_named_transcript_is_bounded_before_it_is_written(self):
        source = (ROOT / "tools/verify_baldosa_windows_extracted_launcher.py"
                  ).read_text()
        for name in ("valid-launch.log", "first-racer-autorelaunch.log",
                     "packaged-options-first.log",
                     "packaged-options-second.log",
                     "packaged-options-damaged.log",
                     "profile-rejected-launch.log"):
            index = source.index(f'(output / "{name}").write_text(')
            self.assertIn("bounded_log(", source[index:index + 140], name)

    def test_rooted_relative_windows_subprocess_receipts_are_bounded_and_verbatim(self):
        import hashlib
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for path, expected_name in (
                ("C:qa-drive-relative-root", "drive-relative-root-refusal.log"),
                ("\\qa-current-drive-root-relative", "current-drive-root-refusal.log"),
            ):
                raw_out = "real stdout \r\n"
                raw_err = "UR-BALDOSA-STARTUP-SAVE-ROOT rejected\n"
                original = subprocess.CompletedProcess(
                    args=["cmd.exe"], returncode=3, stdout=raw_out, stderr=raw_err)
                receipt = verifier.retain_rooted_relative_rejection(root, path, original)
                log = (root / expected_name).read_bytes().decode("utf-8")
                self.assertEqual(
                    log, "STDOUT (actual cmd.exe subprocess):\n" + raw_out +
                    "\nSTDERR (actual cmd.exe subprocess):\n" + raw_err)
                self.assertEqual(receipt["retained_subprocess_transcript"], expected_name)
                self.assertEqual(receipt["process_returncode"], 3)
                self.assertEqual(receipt["expected_exit_code"], 3)
                self.assertTrue(receipt["root_rejection_marker_seen"])
                self.assertEqual(receipt["stdout_utf8_sha256"],
                                 hashlib.sha256(raw_out.encode()).hexdigest())
                self.assertEqual(receipt["stderr_utf8_sha256"],
                                 hashlib.sha256(raw_err.encode()).hexdigest())

    def test_negative_result_is_not_silently_promoted(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as name:
            r = verifier.retain_rooted_relative_rejection(
                Path(name), "C:qa-drive-relative-root",
                subprocess.CompletedProcess(
                    args=["cmd.exe"], returncode=0, stdout="",
                    stderr="not an actual refusal"))
            self.assertEqual(r["process_returncode"], 0)
            self.assertFalse(r["root_rejection_marker_seen"])

    def test_workflow_retains_exactly_those_files_in_a_separate_artifact(self):
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
                    ).read_text()
        block = workflow.split("name: baldosa-win32-extracted-cmd-source-evidence",
                               1)[1].split("- name:", 1)[0]
        # Comments between YAML artifact blocks are NOT retained files.
        # Keep the source transcript allowlist at exactly ten actual paths;
        # do not weaken the strict no-glob and separate-artifact assertions.
        lines = [x.strip() for x in block.split("path: |", 1)[1].splitlines()
                 if x.strip() and not x.lstrip().startswith("#")]
        self.assertEqual(len(lines), 10)
        for line in lines:
            self.assertIn("Baldosa Native Extracted Launcher QA/", line)
            self.assertTrue(line.endswith((".log", "launcher-acceptance.json", "rooted-relative-rejections.json")))
            self.assertNotIn("*", line)  # no blanket globs
        strict = workflow.split("name: baldosa-win32-native-pause-evidence", 1)[1]
        self.assertNotIn("valid-launch.log", strict.split("- name:", 1)[0])
        self.assertNotIn("rooted-relative-rejections.json", strict.split("- name:", 1)[0])
        self.assertIn("drive-relative-root-refusal.log", workflow)
        self.assertIn("current-drive-root-refusal.log", workflow)


    def test_exact_source_packaged_exit8_is_separate_from_fixed_cmd_evidence(self):
        source = (ROOT / "tools/verify_baldosa_windows_extracted_launcher.py"
                  ).read_text()
        helper = (ROOT / "tools/baldosa_win32_live_postraw_sharing_denial.py"
                  ).read_text()
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
                    ).read_text()
        # Source fixture, guest route and seed are all required together,
        # never a fake launcher stub, new SRAM writer or installed ROM.
        for marker in (
            "save_fault_fixture", "save_fault_seed", "save_fault_script",
            "packaged_launcher=launcher",
            'packaged_live_original_save_failure_exit_8',
            'require_archive_unchanged(archive, approved_archive_sha256)',
        ):
            self.assertIn(marker, source)
        self.assertIn("native_denied_process_return_code", helper)
        self.assertIn("native_source_pe_sha256", helper)
        self.assertIn("packaged_launcher_sha256", helper)
        self.assertIn('packaged_save_failure["native_source_pe_sha256"]', source)
        self.assertIn("UR-BALDOSA-SAVE-FAILED: This game session", helper)
        self.assertIn("kernel_replace_probe_winerror", helper)
        self.assertIn("native_modern_race_entry_script(1)", helper)
        self.assertIn("source_pause_frame = 2200", helper)
        self.assertIn('"UR_BALDOSA_MODERN_ROOT_KEY_SMOKE"', helper)
        self.assertIn("original Modern 1P Play", helper)
        self.assertIn("baldosa-win32-packaged-save-refusal-source-bytes", workflow)
        separate = workflow.split(
            "name: baldosa-win32-packaged-save-refusal-source-bytes", 1
        )[1].split("- name:", 1)[0]
        self.assertIn("native_real_win32_live_postraw_typed_denial", separate)
        self.assertIn("fault-bytes/**", separate)
        fixed = workflow.split(
            "name: baldosa-win32-extracted-cmd-source-evidence", 1
        )[1].split("- name:", 1)[0]
        self.assertNotIn("native_real_win32_live_postraw_typed_denial", fixed)
        self.assertNotIn("fault-bytes/**", fixed)


    def test_interactive_recovery_q_console_is_separate(self):
        source = (ROOT / "tools/baldosa_win32_interactive_recovery_q.py"
                  ).read_text()
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
                    ).read_text()
        for marker in (
            'kernel.AttachConsole(pid)', 'kernel.WriteConsoleInputW(',
            '"CONIN$"', 'creationflags=subprocess.CREATE_NEW_CONSOLE',
            'genuine_win32_console_key_event',
            'proc.returncode != 7',
            'post != pre', 'native-sram-manual-archive-*.bin',
        ):
            self.assertIn(marker, source)
        self.assertIn("baldosa-win32-interactive-recovery-q", workflow)
        evidence = workflow.split(
            "name: baldosa-win32-interactive-recovery-q", 1
        )[1].split("- name:", 1)[0]
        self.assertIn("interactive-console.log", evidence)
        self.assertIn("interactive-q-result.json", evidence)
        self.assertIn("source-bytes/**", evidence)
        self.assertIn('retain_stage("before-Q", pre)', source)
        self.assertIn('retain_stage("after-Q", post)', source)
        self.assertIn("len(receipts) == 8", source)
        self.assertIn("digest(verified_rom.read_bytes()) != USA_SHA256", source)
        self.assertIn("shutil.copyfile(verified_rom, installed)", source)
        self.assertIn("installed.unlink(missing_ok=True)", source)
        self.assertIn('["cmd.exe", "/d", "/c", "call", str(wrapper)]', source)
        original = workflow.split(
            "name: baldosa-win32-extracted-cmd-source-evidence", 1
        )[1].split("- name:", 1)[0]
        self.assertNotIn("interactive-console.log", original)
        self.assertNotIn("interactive-q-result.json", original)
        self.assertNotIn("fault-bytes/**", original)

if __name__ == "__main__":
    unittest.main()
