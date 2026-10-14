"""Adversarial original-Snes9x HDMA WRAM writer research tests only."""
import json
from pathlib import Path
import tempfile
import unittest
from tools import instrument_snesref_qa08_hdmacolour_table_writers as instrument
from tools import analyze_snesref_qa08_hdmacolour_table_writers as analyze


def fake_source():
    return '#include "memmap.h"\nvoid S9xMainLoop (void)\n{\n'+instrument.OPCODE+'\n}\n'

def native_receipt():
    rows = [
        {"A_bus_source":"7E:"+addr,"COLDATA_written_byte":"0x"+value}
        for addr,value in analyze.SOURCES.items()
    ]
    rows.insert(1,dict(rows[0]))
    return {"schema":"qa08-native-HDMA-COLDATA-original-source-provenance/1",
            "direct_native_HDMA_COLDATA_written_bytes":7,
            "HDMA_channels_recorded":{"5":7}, "records":rows}


def event(pc,addr,after,*,before="00",frame=2208,v=110):
    return (f"UR_QA08_COLDATA_TABLE_WRITER frame={frame} v={v} "
            f"pc={pc} addr=7E:{addr} before={before} after={after}")


class OriginalColourTableProducerTests(unittest.TestCase):
    def test_producer_probe_exact_guest_dispatch_anchor_and_idempotence(self):
        source=instrument.patch_source(fake_source())
        self.assertEqual(source.count("UR_QA08_COLDATA_TABLE_WRITER frame="),1)
        self.assertIn("UR_QA08_ORIGINAL_WRITER_FRAME_FIRST",source)
        self.assertIn("UR_QA08_ORIGINAL_WRITER_FRAME_LAST",source)
        self.assertIn("b-a <= 256ul",source)
        self.assertIn('#include <stdlib.h>',source)
        self.assertIn('0x2084 + j',source)
        self.assertEqual(source.count("(*Opcodes[Op].S9xOpcode)();"),1)
        with self.assertRaisesRegex(ValueError,"already present"):
            instrument.patch_source(source)
        with self.assertRaisesRegex(ValueError,"layout changed"):
            instrument.patch_source(fake_source().replace(instrument.OPCODE,"// missing"))

    def test_exact_six_guest_source_bytes_are_only_candidate_PCs(self):
        with tempfile.TemporaryDirectory() as tmp:
            original=Path(tmp)/"orig.log"
            native=Path(tmp)/"native.json"
            native.write_text(json.dumps(native_receipt()))
            original.write_text("\n".join(
                event("81A590",addr,value,before="00")
                for addr,value in analyze.SOURCES.items()
            )+"\n")
            result=analyze.report(original,native)
            self.assertEqual(result["original_emulator_writer_events"],6)
            self.assertEqual(result["distinct_executed_guest_PCs"],{"81A590":6})
            self.assertTrue(result["all_six_native_table_source_bytes_matched_at_last_observed_write"])
            self.assertFalse(result["ROM_PC_producer_causality_proven"])
            self.assertFalse(result["paired_identical_original_native_input_and_frame_verified"])

    def test_wrong_original_bytes_do_not_fake_complete_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            original=Path(tmp)/"orig.log"
            native=Path(tmp)/"native.json"
            native.write_text(json.dumps(native_receipt()))
            original.write_text("\n".join(
                event("81A590",addr,"00" if addr=="2089" else value,before="FF")
                for addr,value in analyze.SOURCES.items()
            )+"\n")
            result=analyze.report(original,native)
            self.assertEqual(len(result["last_guest_writer_matching_native_source_value"]),5)
            self.assertFalse(result["all_six_native_table_source_bytes_matched_at_last_observed_write"])

    def test_overflow_incorrect_native_or_forged_original_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            original=Path(tmp)/"orig.log"
            native=Path(tmp)/"native.json"
            native.write_text(json.dumps(native_receipt()))
            original.write_text(event("81A590","2086","2F",before="00")+
                                "\nUR_QA08_COLDATA_TABLE_WRITER_OVERFLOW limit=4096\n")
            with self.assertRaisesRegex(ValueError,"truncated"):
                analyze.report(original,native)
            original.write_text(event("81A590","2064","2F",before="00")+"\n")
            with self.assertRaisesRegex(ValueError,"WRAM"):
                analyze.report(original,native)
            original.write_text(event("81A590","2086","2F",before="2F")+"\n")
            with self.assertRaisesRegex(ValueError,"WRAM"):
                analyze.report(original,native)
            original.write_text(event("81A590","2086","2F")+"\n")
            receipt=native_receipt()
            receipt["HDMA_channels_recorded"]={"4":7}
            native.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError,"native channel5"):
                analyze.report(original,native)


if __name__=="__main__":
    unittest.main()
