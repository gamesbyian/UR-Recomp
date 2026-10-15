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

    def test_workflow_retains_exactly_those_files_in_a_separate_artifact(self):
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
                    ).read_text()
        block = workflow.split("name: baldosa-win32-extracted-cmd-source-evidence",
                               1)[1].split("- name:", 1)[0]
        lines = [x.strip() for x in block.split("path: |", 1)[1].splitlines()
                 if x.strip()]
        self.assertEqual(len(lines), 7)
        for line in lines:
            self.assertIn("Baldosa Native Extracted Launcher QA/", line)
            self.assertTrue(line.endswith((".log", "launcher-acceptance.json")))
            self.assertNotIn("*", line)  # no blanket globs
        strict = workflow.split("name: baldosa-win32-native-pause-evidence", 1)[1]
        self.assertNotIn("valid-launch.log", strict.split("- name:", 1)[0])


if __name__ == "__main__":
    unittest.main()
