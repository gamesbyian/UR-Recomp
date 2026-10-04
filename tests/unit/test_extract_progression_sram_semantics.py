import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import extract_progression_sram_semantics as sem  # noqa: E402


def synthetic_rom() -> bytearray:
    rom = bytearray(0x20000)
    for bank, addr, hexbytes, _ in sem.SIGNATURES.values():
        start = sem.lorom(bank, addr)
        data = bytes.fromhex(hexbytes)
        rom[start:start + len(data)] = data
    return rom


class ProgressionSramSemanticsTests(unittest.TestCase):
    def test_signatures_match_synthetic_rom(self) -> None:
        report = sem.analyze(bytes(synthetic_rom()))
        self.assertTrue(report["all_checks_pass"], report["checks"])
        self.assertEqual(report["layout"]["rider_stats"]["stride"], 8)

    def test_altered_byte_fails_only_its_claim(self) -> None:
        rom = synthetic_rom()
        bank, addr, _, _ = sem.SIGNATURES["failed_is_offset_4"]
        rom[sem.lorom(bank, addr) + 5] ^= 0xFF
        report = sem.analyze(bytes(rom))
        self.assertFalse(report["checks"]["failed_is_offset_4"])
        self.assertEqual(sum(not v for v in report["checks"].values()), 1)

    def test_signatures_do_not_overlap(self) -> None:
        spans = sorted((sem.lorom(b, a), sem.lorom(b, a) + len(bytes.fromhex(h))) for b, a, h, _ in sem.SIGNATURES.values())
        for (_, end), (start, _) in zip(spans, spans[1:]):
            self.assertLessEqual(end, start)

    def test_vs_runtime_reads_stride_8_stats(self) -> None:
        sram = bytearray(0x2000)
        sram[0x0748], sram[0x0749], sram[0x10AD], sram[0x10A9] = 0, 1, 2, 1
        sram[0x061A:0x061C] = (60000).to_bytes(2, "little")
        sram[0x0230], sram[0x0232] = 1, 1
        sram[0x0238], sram[0x023C] = 1, 1
        self.assertTrue(all(sem.vs_runtime(bytes(sram)).values()))
        sram[0x023C] = 0
        self.assertFalse(sem.vs_runtime(bytes(sram))["vs_p2_timeout_counts_played_and_failed"])


if __name__ == "__main__":
    unittest.main()
