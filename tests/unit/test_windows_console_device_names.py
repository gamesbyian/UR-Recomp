"""ROM-free negative controls for Win32 CONIN$ / CONOUT$ package namespace."""
import os
from pathlib import Path
import tempfile
import unittest

from tools import assemble_windows_package as package
from tests.unit.test_assemble_windows_package import WindowsPackageTests


class ConsoleDeviceNamesTest(unittest.TestCase):
    def test_reserved_device_names_have_one_portable_classifier(self):
        for component in (
            "CON", "con.txt", "PRN.bin", "LPT¹.cfg", "com².log",
            "CONIN$", "CONOUT$", "conin$.txt", "ConOut$.dat",
        ):
            with self.subTest(component=component):
                self.assertTrue(package.is_windows_device_component(component))
                with self.assertRaisesRegex(ValueError, "Windows-reserved device"):
                    package.validate_windows_portable_paths(
                        {"mods/preloaded/" + component + "/asset.bin"},
                        context="portable fixture")
        for component in ("connect.txt", "conin-file.txt", "CONIN$$.txt",
                          "LPT10.cfg", "normal.cfg"):
            with self.subTest(accepted=component):
                self.assertFalse(package.is_windows_device_component(component))
                package.validate_windows_portable_paths(
                    {"mods/preloaded/" + component}, context="fixture")

    @unittest.skipIf(os.name == "nt", "Win32 cannot create console-device filenames")
    def test_rejected_mod_source_never_replaces_existing_completed_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = WindowsPackageTests()
            build, rom = fixture.make_inputs(root)
            mods = build / "mods" / "preloaded" / "packages"
            output = root / "completed-package"
            output.mkdir()
            sentinel = output / "keep-previous-release.txt"
            sentinel.write_text("previous bytes", encoding="utf-8")
            for name in ("CONIN$.txt", "CONOUT$.dat"):
                with self.subTest(name=name):
                    invalid = mods / name
                    invalid.write_text("file not valid on Windows", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "Windows-reserved device"):
                        package.assemble(build, rom, output, "negative-preflight")
                    self.assertEqual(sentinel.read_text(encoding="utf-8"),
                                     "previous bytes")
                    invalid.unlink()


if __name__ == "__main__":
    unittest.main()
