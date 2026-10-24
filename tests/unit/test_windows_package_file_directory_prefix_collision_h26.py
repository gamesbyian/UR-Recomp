"""ROM-free package ZIP extraction namespace regression (H26 recovery follow-up).

Source provenance: Evidence Drive archive 142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ,
H26 nested qa04_zip_preflight.py SHA-256
28728223fadf9fc7cb2debd60e3a909ae1946220901b0501af1e96c5960a71e2
and current main package validator feece6a2cb7ab99151c08b243911d75a94eceda3.
This is an independently derived current-package test, not publication of any
held archive source. No ROM bytes, Windows execution or release QA.
"""
import unittest
from tools import assemble_windows_package as package


class PackageZipFileDirectoryPrefixTests(unittest.TestCase):
    def test_mod_file_and_its_child_refuse(self):
        for files in (
            {"mods/preloaded/cache", "mods/preloaded/cache/data.bin"},
            {"mods/a", "mods/a/b/c"},
            {"mods/A", "mods/a/child.bin"},
        ):
            with self.subTest(files=sorted(files)):
                with self.assertRaisesRegex(ValueError, "file/directory prefix collision"):
                    package.validate_windows_portable_paths(files, context="test package")

    def test_required_package_path_consumer_refuses_same_collision(self):
        paths = set(package.REQUIRED_PACKAGE_FILES) | {
            "mods/assets/catalog", "mods/assets/catalog/item.toml",
        }
        with self.assertRaisesRegex(ValueError, "file/directory prefix collision"):
            package.validate_required_package_paths(paths)

    def test_siblings_and_real_directory_prefixes_still_allowed(self):
        paths = set(package.REQUIRED_PACKAGE_FILES) | {
            "mods/assets/catalog/item.toml",
            "mods/assets/catalog/other.toml",
            "mods/assets/catalogue",
            "mods/assets/catalog2",
        }
        package.validate_required_package_paths(paths)
        self.assertTrue(package.validate_windows_portable_paths(
            {"mods/a/x", "mods/a/y", "mods/a2"}, context="test package") is None)


if __name__ == "__main__":
    unittest.main()
