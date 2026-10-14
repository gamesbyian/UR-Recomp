"""Executed Snes9x 65816 original channel-7 table source, no fake PPU result."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools import instrument_snesref_qa08_hdmacolour_table_writers as instrument
from tools import analyze_snesref_qa08_inidisp_table_writers as analyze

HANDOFF = Path(__file__).resolve().parents[2] / (
    "analysis/data/qa08-original-native-2p-brightness-split-channel7-handoff-20261014.json"
)


def evidence():
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


def snapshot(*, values=(0x6F, 0x0F, 0x02, 0x00, 0x6F, 0x0F)):
    # SYNTHETIC model values; original WRAM table headers not yet measured.
    data = bytearray(analyze.WRAM_LENGTH)
    data[0x2064:0x206A] = bytes(values)
    return bytes(data)


def writers():
    return "\n".join([
        "UR_QA08_INIDISP_TABLE_WRITER frame=1987 v=208 pc=81A590 addr=7E:2064 before=00 after=6F",
        "UR_QA08_INIDISP_TABLE_WRITER frame=1987 v=208 pc=81A590 addr=7E:2065 before=00 after=0F",
        "UR_QA08_INIDISP_TABLE_WRITER frame=1987 v=208 pc=81A590 addr=7E:2066 before=00 after=02",
        "UR_QA08_INIDISP_TABLE_WRITER frame=1987 v=208 pc=81A594 addr=7E:2067 before=FF after=00",
        "UR_QA08_INIDISP_TABLE_WRITER frame=1987 v=208 pc=81A594 addr=7E:2068 before=00 after=6F",
        "UR_QA08_INIDISP_TABLE_WRITER frame=1987 v=208 pc=81A594 addr=7E:2069 before=00 after=0F",
    ])


class OriginalChannel7ExecutedTableTests(unittest.TestCase):
    def test_original_probe_source_qualifies_actual_65816_before_after(self):
        s = instrument.patch_source(
            '#include "memmap.h"\nvoid S9xMainLoop (void)\n{\n'
            + instrument.OPCODE + '\n}\n')
        self.assertIn("UR_QA08_INIDISP_TABLE_WRITER frame=", s)
        self.assertIn("Memory.RAM[0x2064 + j]", s)
        self.assertIn("qa08_brightness_prior[j]", s)
        self.assertIn("UR_QA08_INIDISP_TABLE_WRITER_OVERFLOW", s)
        self.assertIn("qa08_executed_pc", s)
        self.assertEqual(s.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertEqual(s.count("UR_QA08_COLDATA_TABLE_WRITER frame="), 1)
        with self.assertRaises(ValueError):
            instrument.patch_source(s)

    def test_original_snapshot_and_executed_guest_PC_are_separate(self):
        r = analyze.report(writers(), snapshot(), snapshot(), evidence())
        self.assertEqual(r["executed_instruction_WRAM_byte_change_events"], 6)
        self.assertEqual(
            r["distinct_executed_instruction_PC_counts"],
            {"81A590": 3, "81A594": 3})
        self.assertEqual(r["original_65816_PC_candidates_by_table_byte"]["7E:2064"],
                         ["81A590"])
        self.assertEqual(r["original_GO_actual_7E_2064_to_2069_bytes"]["7E:2066"],
                         "0x02")
        self.assertFalse(r["original_ROM_instruction_bytes_proven_from_disassembly"])
        self.assertFalse(r["original_table_descriptor_header_semantics_proven"])
        self.assertFalse(r["physical_SNES_hardware_validation"])

    def test_source_negative_does_not_make_up_an_executed_PC(self):
        r = analyze.report("", snapshot(), snapshot(), evidence())
        self.assertEqual(r["executed_instruction_WRAM_byte_change_events"], 0)
        self.assertEqual(r["status"],
                         "original-source-table-snapshot-only-no-writer-executed-in-windows")
        self.assertTrue(all(not pcs for pcs in
                            r["original_65816_PC_candidates_by_table_byte"].values()))

    def test_non_model_header_is_captured_without_guessing(self):
        r = analyze.report(
            "", snapshot(values=(0xF1, 0x0F, 0x82, 0x00, 0x91, 0x0F)),
            snapshot(), evidence())
        self.assertEqual(r["original_GO_actual_7E_2064_to_2069_bytes"]["7E:2064"],
                         "0xF1")
        self.assertFalse(r["original_table_descriptor_header_semantics_proven"])

    def test_bad_source_log_is_rejected(self):
        for old, new in [
            ("frame=1987", "frame=2560"), ("v=208", "v=262"),
            ("addr=7E:2064", "addr=7E:206A"),
            ("before=00 after=6F", "before=6F after=6F"),
            ("pc=81A590", "pc=81A59Z"),
            ("UR_QA08_INIDISP_TABLE_WRITER frame=",
             "UR_QA08_INIDISP_TABLE_WRITER frame=bogus"),
        ]:
            with self.subTest(mutate=old):
                with self.assertRaises(ValueError):
                    analyze.report(writers().replace(old, new), snapshot(),
                                   snapshot(), evidence())
        with self.assertRaisesRegex(ValueError, "overflowed"):
            analyze.report(
                "UR_QA08_INIDISP_TABLE_WRITER_OVERFLOW limit=4096\n" + writers(),
                snapshot(), snapshot(), evidence())

    def test_wrong_true_source_values_or_unverified_evidence_rejected(self):
        incorrect = snapshot(values=(0x6F, 0x0E, 0x02, 0x00, 0x6F, 0x0F))
        with self.assertRaisesRegex(ValueError, "disagree with live"):
            analyze.report("", incorrect, snapshot(), evidence())
        with self.assertRaisesRegex(ValueError, "128 KiB"):
            analyze.report("", b"", snapshot(), evidence())
        wrong = deepcopy(evidence())
        wrong["original"]["run_id"] = 10
        with self.assertRaisesRegex(ValueError, "handoff changed"):
            analyze.report("", snapshot(), snapshot(), wrong)


if __name__ == "__main__":
    unittest.main()
