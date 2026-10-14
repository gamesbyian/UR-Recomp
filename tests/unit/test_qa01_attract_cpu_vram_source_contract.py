"""Fail-closed QA-01 source/cache contract for the attract CPU-VRAM timing lead."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_attract_cpu_vram_source_contract as m


class AttractCpuVramSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = m.BANK81.read_text(encoding="utf-8")
        cls.bank00 = m.BALDOSA_BANK00.read_text(encoding="utf-8")
        cls.bank81 = m.BALDOSA_BANK81.read_text(encoding="utf-8")

    def test_original_cpu_vram_sites_and_explicit_preflight_limits(self):
        r = m.report(self.source, self.bank00, self.bank81)
        self.assertEqual(r["schema"], m.SCHEMA)
        self.assertEqual(r["original_static_span"], ["81:CD70", "81:D09C"])
        self.assertEqual(r["source_family"], "Hud_InitRace_FastRom")
        self.assertEqual(r["direct_cpu_ppu_address_site_count"], 28)
        self.assertEqual(r["direct_cpu_ppu_data_site_count"], 29)
        self.assertEqual(r["direct_cpu_ppu_data_sites"][0], "81:CD70")
        self.assertEqual(r["direct_cpu_ppu_data_sites"][-1], "81:D09C")
        self.assertEqual(r["direct_cpu_ppu_address_sites"][0], "81:CD7A")
        self.assertEqual(r["separate_decompress_to_vram_source"], "81:BB89")
        self.assertEqual(r["separate_decompress_ppu_low_byte_writer"], "81:BCF4")
        self.assertEqual(r["separate_decompress_ppu_high_byte_writer"], "81:BCEE")
        self.assertIs(r["baldosa_config_has_paced_bus"], True)
        self.assertIs(r["paced_bus_is_globally_requested_via_bank00"], True)
        self.assertEqual(r["strict_usa_complete_event_acceptances"], 0)
        for claim in (
            "source_instruction_width_per_executed_site_proven",
            "actual_original_vram_writes_per_host_frame_proven",
            "host_frame_248_original_pc_execution_proven",
            "native_old_vs_baldosa_master_cycle_parity_proven",
            "upstream_clock_correction_caused_rf014_proven",
        ):
            self.assertIs(r[claim], False, claim)

    def test_archived_source_mutations_rejected(self):
        cases = (
            ("vram_data", "81/CD70: 8D 18 21     STA $2118",
             "81/CD70: 8D 19 21     STA $2119"),
            ("vram_addr", "81/CD7A: 8C 16 21     STY $2116",
             "81/CD7A: 8C 18 21     STY $2118"),
            ("branch", "81/CD51: 4C 7F CE     JMP $CE7F",
             "81/CD51: 4C 7E CE     JMP $CE7E"),
            ("decompress_high", "81/BCEE: 8F 19 21 00  STA $002119",
             "81/BCEC: 8F 18 21 00  STA $002118"),
            ("decompress_low", "81/BCF4: 8F 18 21 00  STA $002118",
             "81/BCF4: 8F 19 21 00  STA $002119"),
            ("width", "81/CD43: C2 30        REP #$30",
             "81/CD43: E2 30        SEP #$30"),
        )
        for name, old, bad in cases:
            with self.subTest(name=name):
                self.assertIn(old, self.source)
                with self.assertRaises(ValueError):
                    m.report(self.source.replace(old, bad), self.bank00, self.bank81)

    def test_unexpected_or_duplicate_cpu_ppu_writer_rejected(self):
        old = "81/CE35: 8D 18 21     STA $2118"
        self.assertIn(old, self.source)
        with self.assertRaisesRegex(ValueError, "site count"):
            m.report(self.source.replace(old, "81/CE35: EA           NOP"),
                     self.bank00, self.bank81)
        with self.assertRaisesRegex(ValueError, "duplicate archived original PC"):
            m.report(self.source + "\n" + old + "\n", self.bank00, self.bank81)

    def test_baldosa_pacing_and_exact_upstream_symbols_required(self):
        self.assertIn("\npaced_bus\n", self.bank00)
        with self.assertRaisesRegex(ValueError, "paced_bus"):
            m.report(self.source,
                     self.bank00.replace("\npaced_bus\n", "\n# paced_bus\n"),
                     self.bank81)
        for symbol in ("symbol 81cd07 Hud_InitRace_FastRom",
                       "symbol 81bb89 Decomp_ToVram"):
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, self.bank81)
                with self.assertRaisesRegex(ValueError, "Baldosa source config"):
                    m.report(self.source, self.bank00,
                             self.bank81.replace(symbol, "# " + symbol))


if __name__ == "__main__":
    unittest.main()
