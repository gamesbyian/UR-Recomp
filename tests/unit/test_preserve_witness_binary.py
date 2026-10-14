"""Synthetic tarballs only; no real candidate or ROM is involved."""
from __future__ import annotations

import hashlib
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import preserve_witness_binary as p  # noqa: E402


def tarball(folder: Path, files: dict[str, bytes]) -> Path:
    path = folder / "shared-modern-native.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return path


class WitnessBinaryRetention(unittest.TestCase):
    def test_exact_executable_is_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = tarball(Path(tmp), {p.EXECUTABLE: b"elf", "x/rom.cfg": b"/path/only"})
            info = p.inspect(path, hashlib.sha256(b"elf").hexdigest())
            self.assertEqual(info["rom_image_files"], 0)
            with self.assertRaises(ValueError):
                p.inspect(path, "0" * 64)

    def test_rom_bytes_or_missing_executable_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with_rom = tarball(Path(tmp), {p.EXECUTABLE: b"elf", "x/game.SFC": b"rom"})
            with self.assertRaises(ValueError):
                p.inspect(with_rom, hashlib.sha256(b"elf").hexdigest())
        with tempfile.TemporaryDirectory() as tmp:
            empty = tarball(Path(tmp), {"other": b""})
            with self.assertRaises(ValueError):
                p.inspect(empty, hashlib.sha256(b"").hexdigest())

    def test_workflow_is_manual_read_only_and_bounded(self):
        wf = (ROOT / ".github/workflows/research-preserve-witness-binary.yml").read_text()
        on = wf.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertIn("workflow_dispatch:", on)
        for trigger in ("push:", "pull_request:", "schedule:"):
            self.assertNotIn(trigger, on)
        self.assertNotIn("contents: write", wf)
        self.assertIn("retention-days: 90", wf)
        self.assertIn("tools/preserve_witness_binary.py", wf)


if __name__ == "__main__":
    unittest.main()
