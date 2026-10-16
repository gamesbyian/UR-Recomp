"""Pure, ROM-free adversarial tests of the independent Windows reader."""
from __future__ import annotations

import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_baldosa_win32_modern_repeatability_qa as qa


class ModernSourceConsumerTests(unittest.TestCase):
    def test_exact_archive_population_and_hash(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "artifact.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("one/log.txt", "actual guest event\n")
                z.writestr("two/report.json", '{"release_gate_credit":0}')
            sha = qa.digest(path.read_bytes())
            correct = {"one/log.txt", "two/report.json"}
            self.assertEqual(set(qa.read_archive(path, sha, correct)), correct)
            with self.assertRaisesRegex(ValueError, "wrapper SHA256 differs"):
                qa.read_archive(path, "f" * 64, correct)
            with self.assertRaisesRegex(ValueError, "missing, extra or duplicate"):
                qa.read_archive(path, sha, {"one/log.txt"})

    def test_duplicate_archive_member_rejected_even_with_matching_wrapper_hash(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "dupe.zip"
            with zipfile.ZipFile(path, "w") as z:
                with self.assertWarns(UserWarning):
                    z.writestr("log.txt", "second source revision")
                    z.writestr("log.txt", "alternative source revision")
            with self.assertRaisesRegex(ValueError, "missing, extra or duplicate"):
                qa.read_archive(path, qa.digest(path.read_bytes()), {"log.txt"})

    def test_in_order_and_unique_guest_events(self):
        qa.ordered_once("source FIRST\nsource SECOND\nsource THIRD", "FIRST", "SECOND", "THIRD")
        for corrupted in ("SECOND\nFIRST\nTHIRD", "FIRST\nSECOND\nSECOND\nTHIRD", "FIRST\nTHIRD"):
            with self.subTest(corrupted=corrupted), self.assertRaises(ValueError):
                qa.ordered_once(corrupted, "FIRST", "SECOND", "THIRD")

    def test_source_and_release_gate_cannot_be_forged(self):
        source, exe = "a" * 40, "b" * 64
        bound = {"github_sha": source, "exe_sha256": exe, "rom_sha256": qa.ROM_SHA}
        good = {"source_binding": bound, "release_gate_credit": 0,
                "physical_gamepad_certified": False}
        self.assertEqual(qa.read_report(json.dumps(good).encode(), "Options", source, exe), good)
        for variant in ({**good, "release_gate_credit": True},
                        {**good, "release_gate_credit": 1},
                        {**good, "physical_gamepad_certified": True},
                        {**good, "source_binding": {**bound, "exe_sha256": "c" * 64}}):
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                qa.read_report(json.dumps(variant).encode(), "Options", source, exe)

    def test_archive_symlink_members_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "symlink.zip"
            with zipfile.ZipFile(path, "w") as z:
                info = zipfile.ZipInfo("log.txt")
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(info, "some-target")
            with self.assertRaisesRegex(ValueError, "symlink/encrypted/oversized"):
                qa.read_archive(path, qa.digest(path.read_bytes()), {"log.txt"})

    def test_event_lines_exclude_host_log_noise(self):
        log = ("host clock 100\nUR_BALDOSA_MODERN_ROOT practice_opened=1\n"
               "script f=19 guest changed\nwallclock 8s\n")
        self.assertEqual(qa.events(log), ["UR_BALDOSA_MODERN_ROOT practice_opened=1",
                                          "script f=19 guest changed"])


if __name__ == "__main__":
    unittest.main()
