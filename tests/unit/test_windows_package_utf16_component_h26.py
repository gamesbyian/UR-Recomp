"""ROM-free Windows package path component limit regressions.

First-party research provenance: H26 Evidence Drive archive
142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ, nested
evidence/agent2-h25.zip -> evidence/agent2-h24.zip ->
prior-bundles/20261020T23-agent2-five-line-recovery.zip ->
evidence/agent2-h22-recovery.zip -> evidence/agent2-h20.zip ->
evidence/agent4-h19-recovery.zip ->
work/tests/test_qa04_win32_component_units.py
SHA-256 05a4e8b37102686eae05f443c07191ef8daf72b0b68f21a974fa6a92349a02bc.

New independent tests of the canonical *shipping package* path validator,
not publication of the older evidence ZIP parser. No physical Windows
extraction, copyrighted ROM material or release QA gate credit.
"""
import unittest

from tools import assemble_windows_package as pkg


class WindowsPackageComponentLengthTests(unittest.TestCase):
    def test_256_ascii_utf16_units_rejected_even_in_nested_mod_path(self):
        for name in ("a" * 256 + ".txt", "x/" + "a" * 256 + ".txt"):
            with self.subTest(name=name[:16]):
                with self.assertRaisesRegex(ValueError, "UTF-16"):
                    pkg.validate_windows_portable_paths(
                        {"mods/" + name}, context="test package")

    def test_supplementary_unicode_is_two_utf16_units(self):
        too_long = "\U0001f600" * 126 + ".txt"  # 256 UTF-16 units
        with self.assertRaisesRegex(ValueError, "UTF-16"):
            pkg.validate_windows_portable_paths(
                {"mods/" + too_long}, context="test package")
        okay = "\U0001f600" * 125 + ".txt"  # 254 UTF-16 units
        pkg.validate_windows_portable_paths(
            {"mods/" + okay}, context="test package")

    def test_255_utf16_units_and_sibling_directory_still_allowed(self):
        okay = "a" * 251 + ".txt"
        self.assertEqual(len(okay.encode("utf-16-le")) // 2, 255)
        pkg.validate_windows_portable_paths(
            {"mods/" + okay, "mods/next/file.bin"}, context="test package")

    def test_lone_utf16_surrogate_rejected_with_bounded_value_error(self):
        with self.assertRaisesRegex(ValueError, "UTF-16"):
            pkg.validate_windows_portable_paths(
                {"mods/bad\ud800name.txt"}, context="test package")

    def test_shipping_archive_consumer_uses_same_validator(self):
        filenames = set(pkg.REQUIRED_PACKAGE_FILES) | {
            "mods/assets/" + ("b" * 256) + ".bin"
        }
        with self.assertRaisesRegex(ValueError, "UTF-16"):
            pkg.validate_required_package_paths(filenames, context="archive package")


if __name__ == "__main__":
    unittest.main()
