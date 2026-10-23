"""ROM-free regression for destructive Windows portable-package output aliases.

Run with: python -m unittest tests.unit.test_windows_package_output_symlink
"""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from tools import assemble_windows_package as package_tool


class WindowsPackageOutputSymlinkTests(unittest.TestCase):
    @staticmethod
    def make_inputs(root: Path) -> tuple[Path, Path]:
        build = root / "build"
        build.mkdir()
        (build / package_tool.EXE_NAME).write_bytes(b"synthetic executable")
        (build / package_tool.ROM_CONFIG_NAME).write_bytes(b"synthetic config")
        catalog = build / "mods" / "preloaded" / "packages"
        catalog.mkdir(parents=True)
        (catalog / "catalog.json").write_bytes(b"{}\n")
        rom = root / "synthetic-input.sfc"
        rom.write_bytes(b"synthetic data, not a game ROM")
        return build, rom

    def make_alias(self, alias: Path, target: Path) -> None:
        try:
            alias.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"directory symlinks unavailable: {exc}")

    def test_existing_output_symlink_never_deletes_unrelated_directory(self):
        with tempfile.TemporaryDirectory(prefix="ur-package-output-") as tmp:
            root = Path(tmp)
            build, rom = self.make_inputs(root)
            unrelated = root / "unrelated-user-data"
            unrelated.mkdir()
            sentinel = unrelated / "important.txt"
            sentinel.write_text("KEEP", encoding="ascii")
            alias = root / "portable-output"
            self.make_alias(alias, unrelated)

            with self.assertRaisesRegex(ValueError, "symbolic link"):
                package_tool.assemble(build, rom, alias, "symlink-test")

            self.assertTrue(alias.is_symlink())
            self.assertEqual(sentinel.read_text(encoding="ascii"), "KEEP")
            self.assertEqual([p.name for p in unrelated.iterdir()], ["important.txt"])

    def test_dangling_output_symlink_is_rejected_without_replacement(self):
        with tempfile.TemporaryDirectory(prefix="ur-package-output-") as tmp:
            root = Path(tmp)
            build, rom = self.make_inputs(root)
            target = root / "missing-target"
            alias = root / "portable-output"
            self.make_alias(alias, target)

            with self.assertRaisesRegex(ValueError, "symbolic link"):
                package_tool.assemble(build, rom, alias, "symlink-test")

            self.assertTrue(alias.is_symlink())
            self.assertFalse(target.exists())

    def test_ordinary_output_directory_can_still_be_replaced(self):
        with tempfile.TemporaryDirectory(prefix="ur-package-output-") as tmp:
            root = Path(tmp)
            build, rom = self.make_inputs(root)
            output = root / "portable-output"
            output.mkdir()
            (output / "old-file.txt").write_text("obsolete", encoding="ascii")

            manifest = package_tool.assemble(build, rom, output, "symlink-test")

            self.assertEqual(manifest["source_revision"], "symlink-test")
            self.assertFalse((output / "old-file.txt").exists())
            self.assertTrue((output / package_tool.EXE_NAME).is_file())
            self.assertTrue((output / package_tool.MANIFEST_NAME).is_file())


if __name__ == "__main__":
    unittest.main()
