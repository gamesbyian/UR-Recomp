"""Adversarial original Snes9x 65816 fetched-ROM-source verification."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools import check_qa08_original_channel7_opcode_bytes as source
from tools import instrument_snesref_qa08_hdmacolour_table_writers as instrument

HANDOFF = (Path(__file__).resolve().parents[2] /
    "analysis/data/qa08-original-channel7-65816-writer-artifact-handoff-20261014.json")


def evidence():
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


def original_report():
    h = evidence()
    byaddr = {addr: [] for addr in h["original_GO_table_bytes"]}
    for pc, addr in PCS.items():
        byaddr[addr].append(pc)
    return {
        "schema": source.WRITERS,
        "status": "executed-65816-table-write-observed",
        "original_GO_six_byte_table_SHA256": h["original_GO_table_six_byte_sha256"],
        "original_GO_actual_7E_2064_to_2069_bytes": h["original_GO_table_bytes"],
        "executed_instruction_WRAM_byte_change_events": 1403,
        "distinct_executed_instruction_PC_counts": h["original_source_distinct_writer_PCs"],
        "original_65816_PC_candidates_by_table_byte": byaddr,
    }


PCS = {
    "808625": "7E:2065", "80884C": "7E:2065",
    "808850": "7E:2069", "82D67D": "7E:2064",
    "82D683": "7E:2065", "82D689": "7E:2066",
    "82D695": "7E:2068", "82D699": "7E:2069",
}


def logs():
    lines = []
    for pc, destination in PCS.items():
        bank, address = destination.split(":")
        bytestr = f"8F{int(address,16)&255:02X}{int(address,16)>>8:02X}{bank}"
        lines.append(
            f"UR_QA08_INIDISP_TABLE_OPCODE frame=1781 v=174 pc={pc} "
            f"op=8F oplen=4 bytes={bytestr} mapped=1 fetched=1")
    return lines


class ExecutedOriginalOpcodeByteTests(unittest.TestCase):
    def test_source_hook_retains_real_opcode_preinstruction_identity(self):
        wrapped = instrument.patch_source(
            '#include "memmap.h"\nvoid S9xMainLoop (void)\n{\n' +
            instrument.OPCODE + '\n}\n')
        self.assertIn("UR_QA08_INIDISP_TABLE_OPCODE frame=", wrapped)
        self.assertIn("CPU.PCBase[Registers.PCw + k]", wrapped)
        self.assertIn("ICPU.S9xOpLengths[Op]", wrapped)
        self.assertEqual(wrapped.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertEqual(wrapped.count("UR_QA08_INIDISP_TABLE_WRITER frame="), 1)

    def test_exact_eight_independently_known_pcs_from_synthetic_ROM_reads(self):
        j = source.check("\n".join(logs()), original_report(), evidence())
        self.assertEqual(j["actual_unique_original_65816_writer_PCs"], 8)
        self.assertTrue(j["every_executed_writer_PC_ROM_bytes_observed"])
        self.assertTrue(j["all_store_destinations_match_original_WRAM_changes"])
        self.assertFalse(j["native_original_PPU_scanline_timing_or_global_DMA_correction_proven"])
        self.assertFalse(j["physical_SNES_hardware_or_HD_art_approved"])

    def test_source_PCs_bytes_destination_and_mapping_fail_closed(self):
        l = "\n".join(logs())
        for a, b in [
            ("pc=808625", "pc=808626"),
            ("frame=1781", "frame=2560"),
            ("v=174", "v=262"),
            ("op=8F", "op=AE"),
            ("oplen=4", "oplen=5"),
            ("mapped=1", "mapped=0"),
            ("fetched=1", "fetched=0"),
            ("bytes=8F65207E", "bytes=0065207E"),
        ]:
            with self.subTest(bad=a):
                with self.assertRaises(ValueError):
                    source.check(l.replace(a, b, 1), original_report(), evidence())
        with self.assertRaises(ValueError):
            source.check("\n".join(logs()[:-1]), original_report(), evidence())
        with self.assertRaisesRegex(ValueError, "overflow"):
            source.check(l + "\nUR_QA08_INIDISP_TABLE_OPCODE_OVERFLOW",
                         original_report(), evidence())

    def test_repeat_original_PC_can_only_repeat_unchanged_bytes(self):
        l = logs()
        j = source.check("\n".join(l + l), original_report(), evidence())
        self.assertEqual(j["actual_opcode_observation_records"], 16)
        tampered = l[0].replace("bytes=8F65207E", "bytes=8F66207E")
        with self.assertRaisesRegex(ValueError, "different instruction bytes"):
            source.check("\n".join(l + [tampered]), original_report(), evidence())

    def test_source_handoff_mutation_and_untrusted_WRAM_writer_rejected(self):
        wrong = deepcopy(evidence())
        wrong["original_GO_table_bytes"]["7E:2064"] = "0x6E"
        with self.assertRaises(ValueError):
            source.check("\n".join(logs()), original_report(), wrong)
        w = original_report()
        w["distinct_executed_instruction_PC_counts"]["82D67D"] = 2
        with self.assertRaisesRegex(ValueError, "source changed"):
            source.check("\n".join(logs()), w, evidence())


if __name__ == "__main__":
    unittest.main()
