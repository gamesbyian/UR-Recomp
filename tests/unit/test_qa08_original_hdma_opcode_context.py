"""Fail-closed original opcode-fetch source and 18 executed WRAM PC checks."""
import json
from pathlib import Path
import tempfile
import unittest

from tools import instrument_snesref_qa08_hdma_opcode_context as patch
from tools import check_qa08_original_hdma_opcode_context as checker


def original_fixture():
    return ('#include "memmap.h"\n'
            'void S9xMainLoop (void)\n{\n'
            'Op = CPU.PCBase[Registers.PCw];\n'
            +patch.ANCHOR+"\n}\n")


def accepted():
    pcs=[0x82D5D8+i*4 for i in range(18)]
    return {
        "schema":checker.CENSUS_SCHEMA,
        "original_USA_ROM_SHA256":
            "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        "original_Snes9x_source_run":38510398955,
        "source_changed_WRAM_byte_record_count":18,
        "original_frame_coverage_start":0,
        "original_frame_coverage_end_inclusive":2559,
        "full_original_native_same_input_parity_proven":False,
        "source_byte_changes":[
            {"executed_65816_PC":f"{pc:06X}",
             "WRAM_address":f"{0x2084+i:04X}",
             "after":"04",
             "matches_accepted_native_COLDATA_source":i%2==0}
            for i,pc in enumerate(pcs)
        ],
    }


def trace_line(pc,*,op="A9",first="A9",frame=1781,mapped=1,
               fetched=1,length=2):
    return (f"UR_QA08_ORIGINAL_HDMA_OPCODE frame={frame} pc={pc:06X} "
            f"op={op} oplen={length} bytes={first}040000 "
            f"mapped={mapped} fetched={fetched}")


class NativeOriginalWriterOpcodeSourceTests(unittest.TestCase):
    def test_disposable_source_exact_anchor_and_strict_disarm(self):
        out=patch.patch_source(original_fixture())
        self.assertIn("UR_QA08_ORIGINAL_HDMA_OPCODE_FRAME",out)
        self.assertIn("v == 1781UL",out)
        self.assertIn("CPU.PCBase[qa08_codepc + n]",out)
        self.assertIn("mapped && opbytes[0] == Op",out)
        self.assertEqual(out.count("(*Opcodes[Op].S9xOpcode)();"),1)
        self.assertEqual(out.count("UR_QA08_ORIGINAL_HDMA_OPCODE frame="),1)
        with self.assertRaisesRegex(ValueError,"already present"):
            patch.patch_source(out)
        with self.assertRaisesRegex(ValueError,"anchor changed"):
            patch.patch_source(original_fixture().replace(patch.ANCHOR,"// omitted"))

    def test_all_18_source_observed_original_PC_opcodes_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            data=accepted()
            census=root/"census.json"
            census.write_text(json.dumps(data))
            log=root/"original.log"
            log.write_text("\n".join(trace_line(int(x["executed_65816_PC"],16))
                for x in data["source_byte_changes"])+"\n")
            report=checker.check(log,census)
            self.assertEqual(report["independently_source_accepted_WRAM_writer_PCs"],18)
            self.assertEqual(report["actual_executed_original_opcode_records"],18)
            self.assertEqual(report["actual_opcode_sequence"][0]["actual_instruction_bytes_hex"],"A904")
            self.assertFalse(report["original_native_same_input_frame_parity_proven"])

    def test_bad_mapping_bad_byte_bad_frame_missing_writer_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            census=root/"census.json"; data=accepted()
            census.write_text(json.dumps(data))
            log=root/"original.log"
            pcs=[int(x["executed_65816_PC"],16) for x in data["source_byte_changes"]]
            def run(lines):
                log.write_text("\n".join(lines)+"\n")
                return checker.check(log,census)
            base=[trace_line(pc) for pc in pcs]
            for bad in (trace_line(pcs[0],mapped=0),
                        trace_line(pcs[0],first="FF"),
                        trace_line(pcs[0],frame=1782),
                        trace_line(pcs[0],fetched=0)):
                rows=base.copy(); rows[0]=bad
                with self.assertRaisesRegex(ValueError,"unmapped|wrong-frame|mismatched"):
                    run(rows)
            with self.assertRaisesRegex(ValueError,"incomplete"):
                run(base[:-1])
            with self.assertRaisesRegex(ValueError,"overflow"):
                run(base+["UR_QA08_ORIGINAL_HDMA_OPCODE_OVERFLOW frame=1781 max=512"])
            different=data.copy()
            different["original_Snes9x_source_run"]=2
            census.write_text(json.dumps(different))
            with self.assertRaisesRegex(ValueError,"census missing"):
                run(base)


if __name__=="__main__":
    unittest.main()
