"""ROM-free export path controls for Win32 console names and POSIX surrogates."""
import os
from pathlib import Path
import tempfile
import unittest

from tests.unit.test_export_h22_path_boundaries import fixture
from tools.export_baldosa_earned_1p_run import export


class PortableJourneyRootRecovery(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "Windows cannot create these forbidden names")
    def test_root_devices_and_invalid_unicode_keep_previous_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, name in enumerate(
                ("CONIN$", "CONOUT$", "CONIN$.txt", "conout$.dat",
                 "named" + chr(0xdc80))
            ):
                with self.subTest(name=repr(name)):
                    journey, _ = fixture(root, name)
                    output = root / ("existing-output-" + str(index))
                    output.mkdir()
                    sentinel = output / "existing.txt"
                    sentinel.write_text("unchanged", encoding="utf-8")
                    with self.assertRaisesRegex(
                        ValueError, "Nonportable source journey root name"
                    ):
                        export(journey, output)
                    self.assertEqual(sentinel.read_text(encoding="utf-8"),
                                     "unchanged")

    def test_legitimate_unicode_uses_exact_utf16_unit_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # A non-BMP character contributes two UTF-16 code units.
            # Names near the Win32 component-length bound must not raise
            # UnicodeEncodeError, even when rejected for other reasons.
            name = ("a" * 251) + chr(0x1f600)
            journey, _ = fixture(root, name)
            report = export(journey, root / "accepted-export")
            self.assertEqual(report["source_run_filename"], "earned.urrun")


if __name__ == "__main__":
    unittest.main()
