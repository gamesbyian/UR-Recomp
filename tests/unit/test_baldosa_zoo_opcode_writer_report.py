"""Reference-original Zoo per-opcode WRAM instrumentation and fail-closed parser."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import instrument_snesref_zoo_menu_writes as instrument
import baldosa_zoo_opcode_writer_report as report


class ZooOpcodeWriterTest(unittest.TestCase):
    def test_disposable_instrumentation_is_byte_observational_only(self):
        source = "void a() {\n" + instrument.MARKER + "\n}\n"
        patch = instrument.patch(source)
        self.assertEqual(patch.count(instrument.STAMP), 1)
        self.assertIn("UR_QA_ZOO_TRACE_FIRST", patch)
        self.assertIn("UR_QA_ZOO_TRACE_LAST", patch)
        self.assertIn("Memory.RAM[ur_qa_zoo_addr[ur_i]]", patch)
        self.assertIn("ZOOPCWRITE f=%u", patch)
        self.assertIn(instrument.MARKER, source)
        self.assertEqual(patch.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertNotIn("Memory.RAM[ur_qa_zoo_addr[ur_i]] =", patch)
        self.assertIn(0x008B, instrument.TARGETS)
        self.assertIn(0x0187, instrument.TARGETS)
        self.assertIn(0x0B90, instrument.TARGETS)
        self.assertIn(0x0C61, instrument.TARGETS)
        with self.assertRaisesRegex(ValueError, "already installed"):
            instrument.patch(patch)
        with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
            instrument.patch(source.replace(instrument.MARKER, "other();"))

    def test_detects_guest_pc_and_frame_without_awarding_course(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            before, after = bytearray(0x20000), bytearray(0x20000)
            after[0x8B], after[0x0187], after[0x0B90] = 1, 12, 255
            (d / "boundary-05156.wram.bin").write_bytes(before)
            (d / "boundary-05157.wram.bin").write_bytes(after)
            log = ("ZOOPCWRITE f=6761 v=225 pc=8098B3 addr=008B old=00 new=01\n"
                   "ZOOPCWRITE f=6761 v=225 pc=839A1E addr=0187 old=00 new=0C\n"
                   "ZOOPCWRITE f=6765 v=225 pc=839A1E addr=0B90 old=00 new=FF\n")
            v = report.analyze(log, d, scene_entry_frame=1604)
            self.assertEqual(v["unaltered_source_original_boundary_frame_deltas"]
                             ["wram_differing_bytes"], 3)
            self.assertEqual(v["matched_changed_address_count"], 2)
            self.assertEqual(v["unattributed_changed_address_count"], 1)
            self.assertEqual(v["candidate_pc_counts"],
                             {"80:98B3": 1, "83:9A1E": 1})
            self.assertEqual(v["complete_event_qa_credit"], 0)

    def test_rejects_missing_scope_or_truncated_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            a = bytearray(0x20000)
            b = bytearray(a)
            b[0x8B] = 1
            (d / "boundary-05156.wram.bin").write_bytes(a)
            (d / "boundary-05157.wram.bin").write_bytes(b)
            with self.assertRaisesRegex(ValueError, "no traced opcode"):
                report.analyze("ZOOPCWRITE f=4000 v=2 pc=808000 "
                               "addr=008B old=00 new=01", d,
                               scene_entry_frame=1604)
            with self.assertRaisesRegex(ValueError, "no writes"):
                report.analyze("nothing", d, scene_entry_frame=1604)
            with self.assertRaisesRegex(ValueError, "original scene-entry"):
                report.analyze("nothing", d, scene_entry_frame=0)
            (d / "boundary-05157.wram.bin").write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "complete 128 KiB"):
                report.analyze("ZOOPCWRITE f=6761 v=225 pc=808000 "
                               "addr=008B old=00 new=01", d,
                               scene_entry_frame=1604)

    def test_rejects_nonchanging_opcode_deltas(self):
        with self.assertRaisesRegex(ValueError, "unchanged byte"):
            report.parse("ZOOPCWRITE f=6759 v=225 pc=808000 "
                         "addr=008B old=01 new=01")


if __name__ == "__main__":
    unittest.main()
