"""Exact ROM-free -> original ZIP recovery, with fail-closed negative cases."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import assemble_windows_package as pack
from tools.ci.rehydrate_windows_romfree_package import rehydrate

SHA = "9" * 40


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RehydrateWindowsRomfreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rom = self.root / pack.ROM_NAME
        self.rom.write_bytes(b"test-only mock ROM data")
        self.build = self.root / "build"
        self.build.mkdir()
        exe = self.build / pack.EXE_NAME
        exe.write_bytes(b"MZ" + b"mock-executable-no-player-code")
        (self.build / pack.ROM_CONFIG_NAME).write_bytes(pack.ROM_CONFIG_BYTES)
        mod = self.build / "mods" / "preloaded" / "packages" / ".gitkeep"
        mod.parent.mkdir(parents=True)
        mod.write_bytes(b"")
        produced = self.root / "produced"
        pack.assemble(self.build, self.rom, produced, SHA)
        produced_zip = self.root / "producer.zip"
        pack.create_archive(produced, produced_zip)
        self.original_zip_hash = digest(produced_zip)
        self.original_zip_bytes = produced_zip.read_bytes()
        self.artifact = self.root / "artifact"
        bin_root = self.artifact / "windows-romfree-binary"
        bin_root.mkdir(parents=True)
        shutil.copy2(exe, bin_root / pack.EXE_NAME)
        manifest = self.artifact / pack.ARCHIVE_ROOT / pack.MANIFEST_NAME
        manifest.parent.mkdir(parents=True)
        shutil.copy2(produced / pack.MANIFEST_NAME, manifest)
        self.meta = {
            "schema": "ur-windows-smoke-romfree-pe-binding/1",
            "source_commit": SHA,
            "original_zip_uploaded": False,
            "rom_or_player_data_uploaded": False,
            "executable_bytes": exe.stat().st_size,
            "executable_sha256": digest(exe),
            "original_manifest_sha256": digest(manifest),
            "original_portable_zip_sha256": self.original_zip_hash,
        }
        self.binding_path = bin_root / "binding.json"
        self.write_binding()
        self.sidecar = self.artifact / (pack.ARCHIVE_ROOT + ".zip.sha256")
        self.sidecar.write_text(
            f"{self.original_zip_hash}  {pack.ARCHIVE_ROOT}.zip\n",
            encoding="ascii",
        )
        self.output = self.root / "local" / (pack.ARCHIVE_ROOT + ".zip")

    def write_binding(self):
        self.binding_path.write_text(json.dumps(self.meta) + "\n", encoding="utf-8")

    def restore(self):
        return rehydrate(self.artifact, self.rom, self.output, SHA)

    def test_reconstructs_exact_never_uploaded_zip_and_no_original_rom_in_artifact(self):
        report = self.restore()
        self.assertTrue(report["producer_exact_archive_match"])
        self.assertEqual(report["qa_credit"], "none_pending_actual_execution")
        self.assertEqual(self.output.read_bytes(), self.original_zip_bytes)
        self.assertFalse((self.artifact / pack.ROM_NAME).exists())
        self.assertEqual(pack.verify_archive(self.output)["source_revision"], SHA)
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.restore()

    def test_binding_must_match_exact_producer_and_executable(self):
        with self.assertRaisesRegex(ValueError, "source differs"):
            rehydrate(self.artifact, self.rom, self.output, "8" * 40)
        self.meta["source_commit"] = "8" * 40
        self.write_binding()
        with self.assertRaisesRegex(ValueError, "source differs"):
            self.restore()
        self.meta["source_commit"] = SHA
        self.write_binding()
        exe = self.artifact / "windows-romfree-binary" / pack.EXE_NAME
        exe.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "size does not match binding"):
            self.restore()
        self.assertFalse(self.output.exists())

    def test_unknown_mods_never_synthesized_and_wrong_rom_never_used(self):
        manifest_path = self.artifact / pack.ARCHIVE_ROOT / pack.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text())
        manifest["files"].append({
            "path": "mods/preloaded/unknown.lua", "size": 0,
            "sha256": hashlib.sha256(b"").hexdigest(),
        })
        manifest_path.write_bytes(pack.canonical_manifest_bytes(manifest))
        self.meta["original_manifest_sha256"] = digest(manifest_path)
        self.write_binding()
        with self.assertRaisesRegex(ValueError, "unsupported producer assets"):
            self.restore()
        self.assertFalse(self.output.exists())

    def test_inconsistent_original_zip_digest_never_produces_output(self):
        self.meta["original_portable_zip_sha256"] = "0" * 64
        self.write_binding()
        self.sidecar.write_text(
            f"{'0' * 64}  {pack.ARCHIVE_ROOT}.zip\n", encoding="ascii"
        )
        with self.assertRaisesRegex(ValueError, "differs from exact original"):
            self.restore()
        self.assertFalse(self.output.exists())

    def test_disallowed_rom_upload_claim_and_noncanonical_rom_fail_closed(self):
        self.meta["rom_or_player_data_uploaded"] = True
        self.write_binding()
        with self.assertRaisesRegex(ValueError, "ROM-free evidence contract"):
            self.restore()
        self.meta["rom_or_player_data_uploaded"] = False
        self.write_binding()
        self.rom.write_bytes(b"another test ROM")
        with self.assertRaisesRegex(ValueError, "verified ROM differs"):
            self.restore()


if __name__ == "__main__":
    unittest.main()
