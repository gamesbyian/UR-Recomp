"""Bound legacy device aliases in private QA04 packet filenames, not hardware QA.

Recovery lead: H26 Evidence Drive 142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ
  evidence/agent2-h25.zip -> evidence/agent2-h24.zip ->
  prior-bundles/20261020T23-agent2-five-line-recovery.zip ->
  evidence/agent2-h22-recovery.zip -> evidence/agent2-h20.zip ->
  evidence/agent4-h19-recovery.zip ->
  tests/test_qa04_windows_attachment_names.py
Original test member SHA-256:
  21119202ee03b2d647f9f63ab76c37fc21b49a7e7b3ce5afa754c0e9265b97d6
Original validator member SHA-256:
  35047b545ac729d2d83f9bf7122ab0bb60f46222d05c3d1b0e23f458bc43f415

CLOCK$ was historically a DOS device name. This conservatively excludes it
from portable *private evidence packet* paths; modern NTFS behavior is
unverified, so these tests must not claim physical-Windows acceptance.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from check_qa04_physical_windows_packets import safe_member


class QA04LegacyDeviceComponentTests(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "POSIX fixture creates old Windows device-style names")
    def test_legacy_clock_alias_is_not_portable_as_leaf_or_ancestor(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "packet"
            root.mkdir()
            for name in ("CLOCK$", "clock$.txt", "nested/CLOCK$.log"):
                with self.subTest(name=name):
                    path = root / name
                    path.parent.mkdir(exist_ok=True, parents=True)
                    path.write_bytes(b"synthetic packet bytes")
                    with self.assertRaisesRegex(ValueError, "nonportable Win32"):
                        safe_member(root, name)

    @unittest.skipIf(os.name == "nt", "POSIX fixture creates old Windows device-style names")
    def test_legacy_clock_alias_is_not_portable_as_packet_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "ClOcK$"
            root.mkdir()
            (root / "startup.txt").write_bytes(b"synthetic packet bytes")
            with self.assertRaisesRegex(ValueError, "nonportable Win32"):
                safe_member(root, "startup.txt")

    def test_not_all_clock_named_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "packet"
            root.mkdir()
            source = root / "clock$-notes.txt"
            source.write_bytes(b"synthetic packet bytes")
            self.assertEqual(safe_member(root, source.name), source)


if __name__ == "__main__":
    unittest.main()
