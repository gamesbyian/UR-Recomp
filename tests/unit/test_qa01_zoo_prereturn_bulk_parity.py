"""Offline ZIP-only source/native full-memory observer tests; synthetic credit zero."""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_zoo_prereturn_bulk_parity as p


class ZooPreReturnBulkParity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "synthetic.zip"

    def write_fixture(self, *, mutate=None):
        files = {}
        for side, (folder, logpath, entry) in p.SIDES.items():
            lines = []
            for label in p.FRAMES:
                frame = (entry if label == "scene-entered" else
                         entry + int(label.removeprefix("boundary-")))
                desc = ("fb=256x224 RGB565 sram=8192 ppuw=0"
                        if side == "original" else "ok")
                lines.append(f"script f={frame} dump {label} {desc}")
                for mem, n in p.SIZES.items():
                    files[f"{folder}/{label}.{mem}.bin"] = bytes(n)
            files[logpath] = ("\n".join(lines) + "\n").encode()
        if mutate:
            mutate(files)
        with ZipFile(self.archive, "w") as z:
            for name, data in files.items():
                z.writestr(name, data)
        return self.archive

    def analyze(self, mutate=None):
        return p.analyze(self.write_fixture(mutate=mutate), expected_sha=None)

    def test_full_197120_byte_census_keeps_all_three_classes(self):
        data = self.analyze()
        self.assertEqual(data["memory_classes_bytes"],
                         {"wram": 131072, "vram": 65536, "cgram": 512})
        self.assertEqual(len(data["paired_guest_relative_rows"]), 7)
        self.assertEqual(len(data[
            "all_197120_wram_vram_cgram_bytes_identical_at"]), 7)
        self.assertEqual(data["separate_original_native_scene_host_tick"],
                         {"original": 1604, "native": 1606})
        self.assertTrue(all(v["all_three_memory_classes_exact"]
                            for v in data["paired_guest_relative_rows"]))
        self.assertEqual(data["release_complete_usa_event_credit"], 0)
        self.assertFalse(data["historical_executed_artifact_identity_pinned"])
        self.assertFalse(data["original_native_guest_cpu_nmi_beam_phase_equal_proven"])
        self.assertFalse(data["original_native_complete_event_accepted"])

    def test_detect_realistic_transient_ppu_then_work_ram_delta(self):
        def mutation(files):
            first = bytearray(files[
                "native-boundary/dump/boundary-05155.vram.bin"])
            first[100:129] = bytes([1]) * 29
            files["native-boundary/dump/boundary-05155.vram.bin"] = bytes(first)
            second = bytearray(files[
                "native-boundary/dump/boundary-05156.wram.bin"])
            second[100:169] = bytes([1]) * 69
            files["native-boundary/dump/boundary-05156.wram.bin"] = bytes(second)
        data = self.analyze(mutation)
        self.assertTrue(data["source_wram_match_and_transient_vram_at_5155"])
        self.assertTrue(data["next_sample_vram_match_and_wram_mismatch_at_5156"])
        self.assertEqual(len(data[
            "all_197120_wram_vram_cgram_bytes_identical_at"]), 5)
        self.assertEqual(data["release_complete_usa_event_credit"], 0)

    def test_wrong_zip_fingerprint_refuses_executed_source_identity(self):
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, "artifact identity"):
            p.analyze(self.archive)

    def test_missing_duplicate_malformed_host_receipt_refused(self):
        def missing(files):
            files["original-boundary.log"] = files[
                "original-boundary.log"].replace(
                b"script f=6704 dump boundary-05100", b"script f=6703 dump boundary-05100")
        with self.assertRaisesRegex(ValueError, "mistimed"):
            self.analyze(missing)
        def duplicate(files):
            files["native-boundary/log.txt"] += (
                b"script f=6706 dump boundary-05100 ok\n")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.analyze(duplicate)
        def fake_format(files):
            files["original-boundary.log"] = files[
                "original-boundary.log"].replace(
                b"boundary-04800 fb=256x224 RGB565",
                b"boundary-04800 ok RGB565")
        with self.assertRaisesRegex(ValueError, "invalid emulator frame receipt"):
            self.analyze(fake_format)

    def test_missing_truncated_or_symlinked_memory_is_not_bulk_evidence(self):
        target = "original-boundary/boundary-04800.cgram.bin"
        def truncated(files):
            files[target] = b"\0" * 511
        with self.assertRaisesRegex(ValueError, "incorrect cgram"):
            self.analyze(truncated)
        def missing(files):
            files.pop(target)
        with self.assertRaisesRegex(ValueError, "missing, duplicate"):
            self.analyze(missing)
        self.write_fixture()
        with ZipFile(self.archive, "a") as z:
            z.writestr(target, bytes(512))
        with self.assertRaisesRegex(ValueError, "missing, duplicate"):
            p.analyze(self.archive, expected_sha=None)


if __name__ == "__main__":
    unittest.main()
