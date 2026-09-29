from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import analyze_spc_set as spc


def make_spc(name: str, *, common: bytes = b"COMMON", variant: int = 1) -> bytes:
    data = bytearray(0x10200)
    data[: len(spc.MAGIC)] = spc.MAGIC
    data[0x25:0x27] = (0x0600 + variant).to_bytes(2, "little")

    def field(offset: int, length: int, value: str) -> None:
        encoded = value.encode("ascii")[:length]
        data[offset : offset + len(encoded)] = encoded

    field(0x2E, 32, name)
    field(0x4E, 32, "Uniracers")
    field(0x6E, 16, "Tester")

    ram = memoryview(data)[0x100:0x10100]
    ram[0x0FFF] = variant
    ram[0x1000 : 0x1000 + len(common)] = common
    ram[0x1000 + len(common)] = variant
    ram[0x2000] = variant

    data[0x10100 + 0x5D] = 0xFF
    ram[0xFF00:0xFF02] = (0x3000).to_bytes(2, "little")
    ram[0xFF02:0xFF04] = (0x3000).to_bytes(2, "little")
    ram[0x3000] = 1
    ram[0x3001:0x3009] = bytes([variant]) * 8
    return bytes(data)


class SpcSetTests(unittest.TestCase):
    def test_parse_metadata_and_sample_directory(self) -> None:
        snapshot = spc.parse_spc("one.spc", make_spc("Track One"))
        self.assertEqual(snapshot.title, "Track One")
        self.assertEqual(snapshot.game, "Uniracers")
        self.assertEqual(snapshot.dumper, "Tester")
        self.assertEqual(snapshot.dsp[0x5D], 0xFF)

        samples = spc.brr_samples(snapshot)
        self.assertEqual(samples[0]["start"], 0x3000)
        self.assertEqual(samples[0]["blocks"] if "blocks" in samples[0] else 1, 1)
        self.assertEqual(samples[0]["size"], 9)

    def test_zip_analysis_and_pairwise_similarity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "set.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(
                    "a.spc", make_spc("A", common=b"X" * 32, variant=1)
                )
                archive.writestr(
                    "b.spc", make_spc("B", common=b"X" * 32, variant=2)
                )

            report = spc.analyze(path)
            self.assertEqual(report["spc_count"], 2)
            self.assertEqual(
                report["tracks"][0]["sample_directory_hex"], "0xFF00"
            )
            self.assertEqual(report["tracks"][0]["valid_brr_sample_count"], 1)
            self.assertTrue(
                any(
                    row["start"] == 0x1000 and row["length"] >= 32
                    for row in report["common_apu_ranges_min_16"]
                )
            )
            pair = report["pairwise_apu_ram_similarity"][0]
            self.assertLess(pair["equal_bytes"], 0x10000)
            self.assertEqual(len(report["same_index_brr_samples_all_tracks"]), 0)

    def test_identical_brr_sample_detected_across_tracks(self) -> None:
        left = bytearray(make_spc("A", variant=7))
        right = bytearray(make_spc("B", variant=7))
        right[0x25:0x27] = (0x0777).to_bytes(2, "little")
        left_snapshot = spc.parse_spc("a.spc", bytes(left))
        right_snapshot = spc.parse_spc("b.spc", bytes(right))
        self.assertEqual(
            spc.brr_samples(left_snapshot)[0]["sha256"],
            spc.brr_samples(right_snapshot)[0]["sha256"],
        )


if __name__ == "__main__":
    unittest.main()
