"""Synthetic cache/CI contracts; no synthetic ELF can prove emulator gameplay."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.art import mesence_cache_receipt as receipt

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / ".github/workflows/art4k-live-original-mesen-ppu-raw.yml"
SEED = ROOT / ".github/workflows/art4k-mesence-main-cache-seed.yml"
REVISION = "a60e79feb4d6dcced5922d636f9211837d01e381"


class MesenCeCacheTests(unittest.TestCase):
    def prepare(self, tmp):
        root = Path(tmp)
        cache = root / "cache"
        cache.mkdir()
        exe = cache / "Mesen"
        exe.write_bytes(b"\x7fELF" + b"synthetic-binary")
        exe.chmod(0o755)
        (cache / "libmesen.so").write_bytes(b"synthetic-dependency")
        patch = root / "subport.patch"
        patch.write_text("test patch", encoding="utf-8")
        return cache, patch

    def test_sealed_bytes_and_source_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, patch = self.prepare(tmp)
            seal = receipt.seal(cache, REVISION, patch)
            self.assertEqual(receipt.verify(cache, REVISION, patch), seal)
            result = json.loads((cache / receipt.RECEIPT).read_text())
            self.assertEqual(result["schema"], receipt.SCHEMA)
            self.assertEqual(set(result["files"]), {"Mesen", "libmesen.so"})
            with self.assertRaises(FileExistsError):
                receipt.seal(cache, REVISION, patch)

    def test_corrupt_exe_dependency_patch_revision_extra_member_or_receipt_fails(self):
        for mutation in ("exe", "dependency", "patch", "revision", "extra", "receipt"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                cache, patch = self.prepare(tmp)
                receipt.seal(cache, REVISION, patch)
                revision = REVISION
                if mutation == "exe":
                    (cache / "Mesen").write_bytes(b"\x7fELFmodified")
                elif mutation == "dependency":
                    (cache / "libmesen.so").write_bytes(b"modified")
                elif mutation == "patch":
                    patch.write_text("changed")
                elif mutation == "revision":
                    revision = "b" * 40
                elif mutation == "extra":
                    (cache / "extra").write_bytes(b"unexpected")
                else:
                    target = cache / receipt.RECEIPT
                    body = json.loads(target.read_text())
                    body["source_revision"] = "b" * 40
                    target.write_text(json.dumps(body))
                with self.assertRaisesRegex(ValueError, "MesenCE"):
                    receipt.verify(cache, revision, patch)

    def test_symlink_escape_nonexecutable_and_wrong_elf_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, patch = self.prepare(tmp)
            (cache / "libmesen.so").unlink()
            (cache / "libmesen.so").symlink_to(Path(tmp) / "outside")
            (Path(tmp) / "outside").write_bytes(b"private")
            with self.assertRaisesRegex(ValueError, "redirected"):
                receipt.seal(cache, REVISION, patch)
            (cache / "libmesen.so").unlink()
            (cache / "libmesen.so").write_bytes(b"regular")
            (cache / "Mesen").chmod(0o644)
            with self.assertRaisesRegex(ValueError, "executable"):
                receipt.seal(cache, REVISION, patch)
            (cache / "Mesen").chmod(0o755)
            (cache / "Mesen").write_bytes(b"invalid ELF")
            with self.assertRaisesRegex(ValueError, "ELF"):
                receipt.seal(cache, REVISION, patch)

    def test_trusted_main_seed_and_capture_reuse_identical_cache_key(self):
        main = SEED.read_text()
        capture = ORIGINAL.read_text()
        self.assertIn("  workflow_call:", capture)
        self.assertIn("      seed_only:", capture)
        scope = "$" + "{{ !inputs.seed_only }}"
        self.assertIn("      - name: Capture selected or consecutive original MesenCE PPU RAM frames\n        if: " + scope, capture)
        self.assertIn("      - name: Upload SHA-bound original emulator PPU raw RAM states\n        if: " + scope, capture)
        self.assertIn("      - name: Verify canonical ROM\n", capture)
        self.assertIn("        if: " + scope + "\n        run: python3 tools/verify_rom.py", capture)
        self.assertIn("github.ref == 'refs/heads/main'", main)
        self.assertIn("github.repository == 'gamesbyian/UR-Recomp'", main)
        self.assertIn("      seed_only: true", main)
        self.assertIn("    branches: [main]", main)
        self.assertIn("    paths:\n", main)
        self.assertNotIn("  pull_request:", main)
        self.assertIn("uses: ./.github/workflows/art4k-live-original-mesen-ppu-raw.yml", main)
        self.assertEqual(capture.count("mesence-linux-x64-v3-"), 2)
        self.assertIn("actions/cache/restore@v4", capture)
        self.assertIn("actions/cache/save@v4", capture)
        self.assertLess(capture.index("- name: Save verified pinned MesenCE build"),
                        capture.index("- name: Capture selected or consecutive original"))
        self.assertIn("tools/art/mesence_cache_receipt.py verify", capture)
        self.assertIn("tools/art/mesence_cache_receipt.py", main)
        self.assertIn("third_party/src/mesen-for-ai/patches/mesence-lua-input-subport.patch", main)
        self.assertIn("MESENCE_REVISION: " + REVISION, capture)
        self.assertNotIn("reference/roms", main)
        self.assertNotIn("upload-artifact", main)


if __name__ == "__main__":
    unittest.main()
