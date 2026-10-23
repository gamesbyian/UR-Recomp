"""ROM-free regression for package source mod-tree root redirection."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.assemble_windows_package import (
    EXE_NAME,
    ROM_CONFIG_NAME,
    preflight_package_source_budget,
)


class PackageModsRootLinkTests(unittest.TestCase):
    def test_root_symlink_is_rejected_before_output_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build"
            build.mkdir()
            (build / EXE_NAME).write_bytes(b"synthetic PE fixture")
            (build / ROM_CONFIG_NAME).write_text("placeholder\n", encoding="ascii")
            rom = root / "synthetic.sfc"
            rom.write_bytes(b"synthetic ROM fixture, not retail content")
            external = root / "unrelated-mods"
            external.mkdir()
            (external / "external.txt").write_text("synthetic unrelated data")
            mods = build / "mods"
            try:
                mods.symlink_to(external, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"directory symlinks unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "symlink|reparse"):
                preflight_package_source_budget(build, rom, mods)
            self.assertEqual((external / "external.txt").read_text(),
                             "synthetic unrelated data")

    def test_real_mod_directory_still_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build"
            mods = build / "mods"
            mods.mkdir(parents=True)
            (build / EXE_NAME).write_bytes(b"synthetic PE fixture")
            rom = root / "synthetic.sfc"
            rom.write_bytes(b"synthetic ROM fixture, not retail content")
            (mods / "catalog.txt").write_bytes(b"safe")
            preflight_package_source_budget(build, rom, mods)

    def test_nested_symlink_remains_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build"
            mods = build / "mods"
            mods.mkdir(parents=True)
            (build / EXE_NAME).write_bytes(b"synthetic PE fixture")
            rom = root / "synthetic.sfc"
            rom.write_bytes(b"synthetic ROM fixture, not retail content")
            outside = root / "outside.txt"
            outside.write_bytes(b"synthetic")
            try:
                (mods / "linked.txt").symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "symlink|reparse"):
                preflight_package_source_budget(build, rom, mods)


if __name__ == "__main__":
    unittest.main()
