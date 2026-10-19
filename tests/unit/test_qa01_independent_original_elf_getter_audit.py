"""ROM-free adversarial checks for actual compiled ORIGINAL Snes9x callsite audit."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_independent_original_elf_getter_audit as elf


NM = """
0000000000045720 0000000000000618 t S9xGetByte(unsigned int)
0000000000045d40 0000000000000bc8 t S9xGetWord(unsigned int, s9xwrap_t)
0000000000080060 000000000000036d t Op68E0M0()
00000000000e9a10 0000000000000070 t Op68E0M0() [clone .lto_priv.0]
000000000017e9f0 0000000000000b2e t S9xGetWord(unsigned int, s9xwrap_t) [clone .constprop.0]
"""
WORD = """0000000000045d40 <S9xGetWord(unsigned int, s9xwrap_t)>:
   45d40: f3 0f 1e fa      endbr64
   45e18: e8 b3 d2 ff ff call 430d0 <S9xDoHEventProcessing()>
   45e51: e8 ca f8 ff ff call 45720 <S9xGetByte(unsigned int)>
"""
BYTE = """0000000000045720 <S9xGetByte(unsigned int)>:
   45720: f3 0f 1e fa      endbr64
   457d0: e8 fb d8 ff ff call 430d0 <S9xDoHEventProcessing()>
"""
PULL = """0000000000080060 <Op68E0M0()>:
   800b0: 4c 8b 35 11 a1 2e 00 mov 0x2ea111(%rip),%r14 # 36a1c8 <ur_rf063_source_bus_seq>
   800bf: e8 7c 5c fc ff call 45d40 <S9xGetWord(unsigned int, s9xwrap_t)>
   800ea: e8 81 fa fa ff call 2fb70 <getenv@plt>
   80136: e8 35 fa fa ff call 2fb70 <getenv@plt>
   801d8: e8 33 fc fa ff call 2fe10 <fwrite@plt>
   80278: e8 93 fa fa ff call 2fd10 <__fprintf_chk@plt>
"""


class GenuineOriginalELFObserver(unittest.TestCase):
    def evidence(self, word=WORD, byte=BYTE, opcode=PULL):
        symbols = elf.symbol_locations(NM)
        sites = {elf.GET_BYTE: elf.compiled_site(byte),
                 elf.GET_WORD: elf.compiled_site(word),
                 elf.PULL_OPCODE: elf.compiled_site(opcode)}
        return elf.classify(sites, symbols)

    def test_exact_nm_symbol_sizes_not_lto_clone_substitutions(self):
        result = elf.symbol_locations(NM)
        self.assertEqual(result[elf.GET_BYTE]["start"], 0x45720)
        self.assertEqual(result[elf.GET_WORD]["start"], 0x45d40)
        self.assertEqual(result[elf.GET_WORD]["size"], 0xbc8)
        self.assertEqual(result[elf.PULL_OPCODE]["start"], 0x80060)

    def test_out_of_line_getter_uninstrumented_but_opcode_hook_survives(self):
        report = self.evidence()
        self.assertTrue(report["opcode_direct_call_to_uninstrumented_word_getter"])
        self.assertTrue(report["compiled_getbyte_no_direct_RF044_RF063_logger"])
        self.assertTrue(report["compiled_getword_no_direct_RF044_RF063_logger"])
        self.assertTrue(report["compiled_opcode_postcall_sequence_references_present"])
        self.assertEqual(report["sites"][elf.GET_WORD]["direct_getenv_calls"], 0)
        self.assertEqual(report["sites"][elf.PULL_OPCODE]["direct_getenv_calls"], 2)
        self.assertFalse(report["actual_original_executable_guest_instruction_path_proven"])
        self.assertFalse(report["all_other_inlined_or_cloned_original_getters_qualified"])
        self.assertEqual(report["accepted_USA_events"], 0)
        self.assertEqual(report["adjudication"], "HOLD")

    def test_missing_direct_call_cannot_fabricate_original_getter_path(self):
        corrupted = PULL.replace("<S9xGetWord(unsigned int, s9xwrap_t)>",
                                 "<S9xGetWordUnrelated()>")
        with self.assertRaisesRegex(ValueError, "does not directly call"):
            self.evidence(opcode=corrupted)

    def test_instrumented_getter_must_not_still_be_reported_absent(self):
        altered = WORD + "  46001: e8 12 10 00 00 call 2fb70 <getenv@plt>\n"
        report = self.evidence(word=altered)
        self.assertFalse(report["compiled_getword_no_direct_RF044_RF063_logger"])
        self.assertFalse(report["opcode_direct_call_to_uninstrumented_word_getter"])

    def test_missing_multiple_or_overlapping_symbols_refused(self):
        for changes in (NM.replace("S9xGetWord(unsigned int, s9xwrap_t)",
                                   "S9xGetWordOther(int)", 1),
                        NM + "0000000000045d40 0000000000000bc8 t S9xGetWord(unsigned int, s9xwrap_t)\n",
                        NM.replace("0000000000080060", "0000000000045d40")):
            with self.subTest(source=changes), self.assertRaises(ValueError):
                elf.symbol_locations(changes)

    def test_disassembly_requires_actual_instruction_lines(self):
        with self.assertRaisesRegex(ValueError, "empty actual executable"):
            elf.compiled_site("S9xGetWord calls getenv RF044 in a source comment")

    def test_wrong_binary_cannot_pass_pinned_core_digest(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "fake.so"
            file.write_bytes(b"not a genuine source ELF")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                elf.run_binary(file, elf.RF066_CORE_SHA256)
        with self.assertRaisesRegex(ValueError, "missing 64-hex"):
            elf.run_binary(Path("/nonexistent"), "fakehash")


if __name__ == "__main__":
    unittest.main()
