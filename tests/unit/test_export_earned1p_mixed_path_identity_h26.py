"""ROM-free exporter namespace isolation across relative/absolute path aliases.

H26 Evidence archive lineage:
142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ ->
evidence/agent3-h25.zip -> prior/agent3-h24-recovery.zip ->
tests/test_h22_export_destination_isolation.py
(member SHA-256 1245c0af616dc0abfe3b7ed81671fc42e293677cafc4b24dfdd7868ae5fd4ca9).
The old H22 controls cover nested destination paths, not mixed textual roots.
These independently derived tests pin an additional current-main boundary.
No ROM, NTFS reparse handle, real earned gameplay or release credit.
"""
from pathlib import Path
import tempfile
import unittest

from tools import export_baldosa_earned_1p_run as exporter


class ExporterMixedPathIdentityIsolation(unittest.TestCase):
    def test_relative_journey_absolute_nested_destination_refused_before_source_read(self):
        # A temporary root below cwd permits a non-dot-dot relative spelling.
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root = Path(temp)
            source = root / "journey"
            source.mkdir()
            relative_source = Path(root.name) / "journey"
            target = source / "evidence"
            self.assertEqual(relative_source.absolute(), source)
            with self.assertRaisesRegex(ValueError, "outside source journey"):
                exporter.export(relative_source, target)
            self.assertFalse(target.exists())

    def test_absolute_journey_relative_nested_destination_refused_before_source_read(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            root = Path(temp)
            source = root / "journey"
            source.mkdir()
            relative_target = Path(root.name) / "journey" / "evidence"
            self.assertEqual(relative_target.absolute(), source / "evidence")
            with self.assertRaisesRegex(ValueError, "outside source journey"):
                exporter.export(source, relative_target)
            self.assertFalse((source / "evidence").exists())


if __name__ == "__main__":
    unittest.main()
