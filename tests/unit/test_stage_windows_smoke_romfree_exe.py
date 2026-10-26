"""No ROM input is ever opened or copied by the PE-only evidence stage."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "ci"))
import stage_windows_smoke_romfree_exe as m

SHA = "a" * 40


def fixture(root: Path) -> tuple[Path, Path, Path, Path]:
    package = root / "package"
    package.mkdir()
    exe = package / m.EXE
    data = bytearray(512)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3c, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", data, 0x84, 0x8664)
    struct.pack_into("<H", data, 0x98, 0x20b)
    exe.write_bytes(data)
    (package / "Uniracers_USA.sfc").write_bytes(b"PRIVATE ROM DO NOT COPY")
    (package / "player.srm").write_bytes(b"PRIVATE PLAYER DO NOT COPY")
    manifest = {"source_revision": SHA, "files": [{
        "path": m.EXE, "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest()}]}
    (package / "PACKAGE-MANIFEST.json").write_text(json.dumps(manifest))
    archive = root / "UR-Recomp-Windows-x64.zip"
    archive.write_bytes(b"pretend original full ZIP stays private")
    checksum = root / (archive.name + ".sha256")
    checksum.write_text(m.digest(archive) + "  " + archive.name + "\n")
    return package, archive, checksum, root / "evidence"


class RomfreePeStageTests(unittest.TestCase):
    def test_only_executable_and_binding_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            package, archive, checksum, output = fixture(Path(tmp))
            row = m.stage(package, archive, checksum, SHA, output)
            self.assertEqual({p.name for p in output.iterdir()},
                             {m.EXE, "binding.json"})
            self.assertEqual((output / m.EXE).read_bytes(),
                             (package / m.EXE).read_bytes())
            self.assertEqual(json.loads((output / "binding.json").read_text()), row)
            self.assertEqual(row["original_portable_zip_sha256"], m.digest(archive))
            self.assertEqual(row["release_gate_credit"], 0)
            self.assertFalse(row["physical_windows_accepted"])
            self.assertNotIn(b"PRIVATE ROM", (output / m.EXE).read_bytes())

    def test_fail_closed_before_output_on_invalid_inputs(self):
        for kind in ("wrong_source", "wrong_manifest_hash", "wrong_exe",
                     "wrong_checksum", "symlink_exe", "existing_output"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                package, archive, checksum, output = fixture(Path(tmp))
                source = SHA
                if kind == "wrong_source":
                    source = "b" * 40
                elif kind == "wrong_manifest_hash":
                    manifest = package / "PACKAGE-MANIFEST.json"
                    data = json.loads(manifest.read_text())
                    data["files"][0]["sha256"] = "0" * 64
                    manifest.write_text(json.dumps(data))
                elif kind == "wrong_exe":
                    (package / m.EXE).write_bytes(b"not PE")
                elif kind == "wrong_checksum":
                    checksum.write_text("0" * 64 + "  " + archive.name + "\n")
                elif kind == "symlink_exe":
                    if os.name == "nt":
                        continue  # unprivileged Windows may prohibit symlink creation
                    exe = package / m.EXE
                    exe.unlink()
                    exe.symlink_to(archive)
                elif kind == "existing_output":
                    output.mkdir()
                with self.assertRaises((ValueError, OSError)):
                    m.stage(package, archive, checksum, source, output)
                if kind != "existing_output":
                    self.assertFalse(output.exists())

    def test_no_follow_redirected_output_ancestor(self):
        if os.name == "nt":
            self.skipTest("unprivileged Windows symlink creation may be disabled")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package, archive, checksum, _ = fixture(root)
            (root / "redirect").symlink_to(package, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "redirected ancestor"):
                m.stage(package, archive, checksum, SHA, root / "redirect" / "evidence")

    def test_never_write_into_original_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            package, archive, checksum, _ = fixture(Path(tmp))
            with self.assertRaisesRegex(ValueError, "overlaps original package"):
                m.stage(package, archive, checksum, SHA, package / "evidence")


if __name__ == "__main__":
    unittest.main()
