"""Shipping ZIP input bounds and streaming behavior, without large allocations."""
from __future__ import annotations

import pathlib
import tempfile
import unittest
import zipfile
from unittest import mock

from tools import assemble_windows_package as package


class WindowsPackageStreamingBoundsTests(unittest.TestCase):
    def build_zip(self, root: pathlib.Path) -> pathlib.Path:
        build = root / "build"
        build.mkdir()
        (build / package.EXE_NAME).write_bytes(b"exe")
        (build / package.ROM_CONFIG_NAME).write_text("generated-rom-path\n")
        mod = build / "mods" / "preloaded" / "packages"
        mod.mkdir(parents=True)
        (mod / "catalog.json").write_bytes(b"{}\n")
        rom = root / package.ROM_NAME
        rom.write_bytes(b"rom")
        assembled = root / "assembled"
        package.assemble(build, rom, assembled, "test-revision")
        archive = root / "UR-Recomp-Windows-x64.zip"
        package.create_archive(assembled, archive)
        return archive

    def test_streaming_verifier_never_reads_large_payload_wholesale(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = self.build_zip(pathlib.Path(temp))
            # read(name) is allowed only for the bounded manifest/README/config.
            # Payload hashes must use source.open(info).read(fixed-size-chunks).
            actual_zip_class = zipfile.ZipFile

            class RejectUnboundedPayloadRead(actual_zip_class):
                def read(self, name, *args, **kwargs):
                    if str(name).endswith((".exe", ".sfc", "catalog.json")):
                        raise AssertionError("unbounded payload read")
                    return super().read(name, *args, **kwargs)

            with mock.patch.object(package.zipfile, "ZipFile", RejectUnboundedPayloadRead):
                manifest = package.verify_archive(archive)
            self.assertEqual(manifest["source_revision"], "test-revision")

    def test_oversized_zip_entry_rejected_before_decompression(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = self.build_zip(pathlib.Path(temp))
            raw = bytearray(archive.read_bytes())
            central = raw.find(bytes.fromhex("504b0102"))
            self.assertGreaterEqual(central, 0)
            # Central directory uncompressed-size field, while the real stored
            # data is only a few bytes. This test must never allocate 512 MiB.
            raw[central + 24:central + 28] = (
                package.MAX_PACKAGE_FILE_BYTES + 1
            ).to_bytes(4, "little")
            archive.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "exceeds shipping size limits"):
                package.verify_archive(archive)

    def test_sparse_package_input_is_rejected_before_hashing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            oversize = root / "oversize.bin"
            with oversize.open("wb") as handle:
                handle.truncate(package.MAX_PACKAGE_FILE_BYTES + 1)
            with mock.patch.object(
                package, "sha256", side_effect=AssertionError("unexpected hash")
            ):
                with self.assertRaisesRegex(ValueError, "exceeds shipping size limits"):
                    package.package_files(root)

    def test_oversized_source_rejected_before_copy_or_output_removal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            build = root / "build"
            build.mkdir()
            (build / package.EXE_NAME).write_bytes(b"exe")
            (build / package.ROM_CONFIG_NAME).write_bytes(b"config")
            mods = build / "mods" / "preloaded"
            mods.mkdir(parents=True)
            # Legacy mutable state is ultimately removed from the ZIP, but
            # copytree used to copy it *before* deletion. Preflight must still
            # reject a sparse oversized source without copying its contents.
            with (mods / "state.toml").open("wb") as handle:
                handle.truncate(package.MAX_PACKAGE_FILE_BYTES + 1)
            (mods / "catalog.json").write_bytes(b"{}")
            rom = root / package.ROM_NAME
            rom.write_bytes(b"rom")
            output = root / "existing-package"
            output.mkdir()
            marker = output / "previous-success.txt"
            marker.write_text("keep prior package")

            with mock.patch.object(
                package.shutil, "copy2",
                side_effect=AssertionError("source copied before preflight"),
            ):
                with self.assertRaisesRegex(
                    ValueError, "package source exceeds shipping size limits"
                ):
                    package.assemble(build, rom, output, "test-revision")
            self.assertEqual(marker.read_text(), "keep prior package")

    def test_oversized_manifest_is_rejected_before_json_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            manifest = root / package.MANIFEST_NAME
            with manifest.open("wb") as handle:
                handle.truncate(package.MAX_PACKAGE_MANIFEST_BYTES + 1)
            with self.assertRaisesRegex(ValueError, "manifest exceeds shipping size limit"):
                package.verify(root)


if __name__ == "__main__":
    unittest.main()
