"""ROM-free source-revision binding for the extracted Windows CMD launcher.

A self-consistent manifest, README and ZIP digest must not bless a launcher
whose embedded startup build revision still names another source tree.
"""

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools import assemble_windows_package as package_tool


class WindowsLauncherProvenanceTests(unittest.TestCase):
    def make_package(self, root: Path) -> Path:
        build = root / "build"
        build.mkdir()
        (build / package_tool.EXE_NAME).write_bytes(b"synthetic PE fixture")
        (build / package_tool.ROM_CONFIG_NAME).write_text("fixture only\n")
        mods = build / "mods" / "preloaded" / "packages"
        mods.mkdir(parents=True)
        (mods / "catalog.json").write_bytes(b"{}\n")
        rom = root / "synthetic.sfc"
        rom.write_bytes(b"synthetic fixture, not retail ROM content")
        package = root / "portable"
        package_tool.assemble(build, rom, package, "source-before")
        return package

    @staticmethod
    def altered_manifest(manifest: dict) -> dict:
        forged = json.loads(json.dumps(manifest))
        forged["source_revision"] = "source-after"
        readme = package_tool.readme_text("source-after").encode("utf-8")
        for entry in forged["files"]:
            if entry["path"] == package_tool.README_NAME:
                entry["size"] = len(readme)
                entry["sha256"] = hashlib.sha256(readme).hexdigest()
                break
        else:
            raise AssertionError("fixture README missing")
        return forged

    def test_extracted_package_rejects_relabelled_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = self.make_package(Path(tmp))
            package_tool.verify(package)
            manifest_path = package / package_tool.MANIFEST_NAME
            forged = self.altered_manifest(json.loads(manifest_path.read_text()))
            (package / package_tool.README_NAME).write_bytes(
                package_tool.readme_text("source-after").encode("utf-8")
            )
            manifest_path.write_bytes(package_tool.canonical_manifest_bytes(forged))
            with self.assertRaisesRegex(ValueError, "launcher.*source revision"):
                package_tool.verify(package)

    def test_signed_archive_rejects_relabelled_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self.make_package(root)
            original = root / "original.zip"
            package_tool.create_archive(package, original)
            package_tool.verify_archive(original)
            manifest = json.loads((package / package_tool.MANIFEST_NAME).read_text())
            forged = self.altered_manifest(manifest)
            altered = root / "relabelled.zip"
            with zipfile.ZipFile(original) as src, zipfile.ZipFile(altered, "w") as dst:
                for info in src.infolist():
                    payload = src.read(info.filename)
                    if info.filename.endswith("/" + package_tool.MANIFEST_NAME):
                        payload = package_tool.canonical_manifest_bytes(forged)
                    elif info.filename.endswith("/" + package_tool.README_NAME):
                        payload = package_tool.readme_text("source-after").encode("utf-8")
                    dst.writestr(info, payload)
            with self.assertRaisesRegex(ValueError, "launcher.*source revision"):
                package_tool.verify_archive(altered)


if __name__ == "__main__":
    unittest.main()
