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
        cls.bank80_source = m.BANK80.read_text(encoding="utf-8")
        cls.bank82_source = m.BANK82.read_text(encoding="utf-8")
        cls.source = m.BANK81.read_text(encoding="utf-8")
        cls.bank83_source = m.BANK83.read_text(encoding="utf-8")
        cls.bank00 = m.BALDOSA_BANK00.read_text(encoding="utf-8")
        cls.bank81 = m.BALDOSA_BANK81.read_text(encoding="utf-8")

    def test_original_logo_attract_upload_cpu_pc_provenance(self):
        row = m.attract_upload_direct_source_contract(
            self.bank80_source, self.source, self.bank82_source)
        self.assertEqual(row["source_attract_entry_pc"], "80:93FB")
        self.assertEqual(row["source_attract_upload_call_pcs"],
                         ["80:941B", "80:9424"])
        self.assertEqual(row["source_logo_upload_call_pcs"],
                         ["80:B0A6", "80:B0AF"])
        self.assertEqual(row["source_cpu_upload_entry_pc"], "82:B1D8")
        self.assertEqual(row["source_compressed_branch_pc"], "82:B1ED")
        self.assertEqual(row["source_compressed_call_pc"], "82:B216")
        self.assertEqual(row["source_decompress_entry_pc"], "81:BB89")
        self.assertEqual(row["source_decompress_byte_store_pcs"],
                         ["81:BCEE", "81:BCF4"])
        self.assertEqual(row["source_upload_m8_mode"], "82:B1DB SEP #$20")
        for field in (
            "full_source_upload_word_count_executed_proven",
            "actual_original_host_248_278_writer_pcs_observed",
            "selected_original_compression_branch_dynamically_observed",
            "original_memory_speed_at_upload_proven",
            "full_first_load_timing_causality_proven",
        ):
            self.assertIs(row[field], False, field)

    def test_original_upload_call_and_loop_mutations_fail_closed(self):
        cases = (
            ("attract caller", "80/941B: 22 D8 B1 82  JSR $82B1D8",
             "80/941B: 22 D9 B1 82  JSR $82B1D9", "bank80"),
            ("logo caller", "80/B0AF: 22 D8 B1 82  JSR $82B1D8",
             "80/B0AF: 22 D9 B1 82  JSR $82B1D9", "bank80"),
            ("compressed branch", "82/B1ED: F0 19        BEQ $B208",
             "82/B1ED: D0 19        BNE $B208", "bank82"),
            ("low byte", "82/B1F5: 8F 18 21 00  STA $002118",
             "82/B1F5: 8F 19 21 00  STA $002119", "bank82"),
            ("high byte", "82/B1FC: 8F 19 21 00  STA $002119",
             "82/B1FC: 8F 18 21 00  STA $002118", "bank82"),
            ("counter", "82/B201: CA           DEX",
             "82/B201: E8           INX", "bank82"),
            ("compressed upload", "82/B216: 22 89 BB 81  JSR $81BB89",
             "82/B216: 22 89 BA 81  JSR $81BA89", "bank82"),
            ("decompress store", "81/BCEE: 8F 19 21 00  STA $002119",
             "81/BCEE: 8F 18 21 00  STA $002118", "bank81"),
        )
        sources = {"bank80": self.bank80_source,
                   "bank81": self.source, "bank82": self.bank82_source}
        for name, old, bad, owner in cases:
            with self.subTest(name=name):
                self.assertIn(old, sources[owner])
                altered = dict(sources)
                altered[owner] = altered[owner].replace(old, bad)
                with self.assertRaisesRegex(ValueError, "original upload"):
                    m.attract_upload_direct_source_contract(
                        altered["bank80"], altered["bank81"], altered["bank82"])
        duplicated = self.bank82_source + (
            "\n82/B1FC: 8F 19 21 00  STA $002119\n")
        with self.assertRaisesRegex(ValueError, "original upload"):
            m.attract_upload_direct_source_contract(
                self.bank80_source, self.source, duplicated)

    def test_long_store_clock_scenarios_never_claim_executed_first_load(self):
        for memsel, width, old, paced, excess in (
            (0, 1, 40, 38, 2), (0, 2, 48, 44, 4),
            (1, 1, 30, 30, 0), (1, 2, 36, 36, 0),
        ):
            with self.subTest(memsel=memsel, width=width):
                r = m.conditional_long_store_master_clocks(width, memsel)
                self.assertEqual(r["old_uniform_master_clocks"], old)
                self.assertEqual(r["baldosa_paced_master_clocks"], paced)
                self.assertEqual(r["old_minus_paced_master_clocks"], excess)
                self.assertIs(r["actual_source_pc_executed_in_host_window"], False)
                self.assertIs(r["first_load_timing_causality_proven"], False)
        for width, memsel in ((0, 0), (3, 1), (1, -1), (1, 2)):
            with self.subTest(invalid=(width, memsel)):
                with self.assertRaises(ValueError):
                    m.conditional_long_store_master_clocks(width, memsel)

    def test_archived_race_setup_wrapper_caller_chain(self):
        obj = m.hud_direct_caller_source_contract(
            self.source, self.bank82_source)
        self.assertEqual(obj["source_wrapper_pc"], "81:CCE6")
        self.assertEqual(obj["source_wrapper_target_pc"], "81:CD07")
        self.assertEqual(obj["source_race_setup_caller_pc"], "82:DC1A")
        self.assertEqual(obj["race_setup_lap_initialization_pcs"],
                         ["82:DBF7", "82:DBFA"])
        self.assertEqual(obj["race_setup_before_hud_call_pcs"],
                         ["82:DC13", "82:DC17"])
        for claim in (
            "original_cpu_executed_hud_in_host_248_to_278_proven",
            "hud_path_exclusive_vram_writer_in_first_load_proven",
            "all_indirect_callers_excluded",
        ):
            self.assertIs(obj[claim], False)

    def test_original_hud_caller_mutations_and_duplicate_pc_rejected(self):
        caller = "82/DC1A: 22 E6 CC 81  JSR $81CCE6"
        wrapper = "81/CCE6: 20 07 CD     JSR $CD07"
        self.assertIn(caller, self.bank82_source)
        self.assertIn(wrapper, self.source)
        with self.assertRaisesRegex(ValueError, "original HUD caller"):
            m.hud_direct_caller_source_contract(
                self.source,
                self.bank82_source.replace(
                    caller, "82/DC1A: 22 E7 CC 81  JSR $81CCE7"))
        with self.assertRaisesRegex(ValueError, "original HUD caller"):
            m.hud_direct_caller_source_contract(
                self.source.replace(
                    wrapper, "81/CCE6: 20 09 CD     JSR $CD09"),
                self.bank82_source)
        with self.assertRaisesRegex(ValueError, "original HUD caller"):
            m.hud_direct_caller_source_contract(
                self.source, self.bank82_source + "\n" + caller + "\n")
        lap = "82/DBF7: 8D F1 0E     STA $0EF1"
        self.assertIn(lap, self.bank82_source)
        with self.assertRaisesRegex(ValueError, "original HUD caller"):
            m.hud_direct_caller_source_contract(
                self.source,
                self.bank82_source.replace(
                    lap, "82/DBF7: 8D F2 0E     STA $0EF2"))

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

    def test_old_vs_paced_cpu_ppu_write_conditional_master_clocks(self):
        # Effective bank 81 FastROM MEMSEL is not inferred by the source
        # contract. Under slow-ROM mode old uniform instruction charging
        # overprices fast $2118/$2116 PPU register accesses.
        for memsel, width, old, paced, delta in (
            (0, 1, 32, 30, 2),
            (0, 2, 40, 36, 4),
            (1, 1, 24, 24, 0),
            (1, 2, 30, 30, 0),
        ):
            with self.subTest(memsel=memsel, width=width):
                row = m.conditional_abs_store_master_clocks(width, memsel)
                self.assertEqual(row["old_uniform_code_speed_master_clocks"], old)
                self.assertEqual(row["baldosa_paced_bus_master_clocks"], paced)
                self.assertEqual(row["old_minus_paced_master_clocks"], delta)
                self.assertIs(row["actually_executed_first_load_width_or_memsel_proven"], False)
                self.assertIs(row["entire_frame_clock_discrepancy_explained"], False)
        r = m.report(self.source, self.bank00, self.bank81)
        self.assertEqual(len(r["conditional_cpu_store_clock_scenarios"]), 4)
        self.assertEqual(sorted({
            s["old_minus_paced_master_clocks"]
            for s in r["conditional_cpu_store_clock_scenarios"]
        }), [0, 2, 4])

    def test_clock_model_rejects_unknown_width_and_memsel(self):
        for width, memsel in ((0, 0), (3, 0), (-1, 1), (2, 2), (1, -1)):
            with self.subTest(width=width, memsel=memsel):
                with self.assertRaisesRegex(ValueError, "width|MEMSEL"):
                    m.conditional_abs_store_master_clocks(width, memsel)

    def test_exact_original_direct_memsel_writer_contract(self):
        actual = m.memsel_direct_source_writers(
            self.bank80_source, self.bank83_source)
        for key, pc in (
            ("bank80_boot_fastrom_set", "80:91EA"),
            ("bank80_boot_slowrom_reset", "80:92E8"),
            ("bank83_game_fastrom_set", "83:CC6F"),
            ("bank83_other_slowrom_reset", "83:FA39"),
        ):
            self.assertEqual(actual[key], pc)
        for claim in (
            "all_memsel_writers_dynamically_executed_in_first_load_proven",
            "first_load_memsel_value_proven",
            "original_unobserved_indirect_memsel_writers_excluded",
        ):
            self.assertIs(actual[claim], False)

    def test_mutated_duplicate_memsel_writers_and_boot_order_rejected(self):
        with self.assertRaisesRegex(ValueError, "MEMSEL opcode"):
            m.memsel_direct_source_writers(
                self.bank80_source.replace(
                    "80/92E8: 9C 0D 42     STZ $420D",
                    "80/92E8: 9C 0C 42     STZ $420C"),
                self.bank83_source)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            m.memsel_direct_source_writers(
                self.bank80_source +
                "\n80/91EA: 8D 0D 42     STA $420D\n",
                self.bank83_source)
        with self.assertRaisesRegex(ValueError, "MEMSEL opcode"):
            m.memsel_direct_source_writers(
                self.bank80_source, self.bank83_source.replace(
                    "83/CC6D: A9 01        LDA #$01",
                    "83/CC6D: A9 00        LDA #$00"))

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
