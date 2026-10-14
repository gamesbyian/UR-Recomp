"""Fail-closed source contracts for seven genuine channel5 mode1 SETINI bytes."""
import json
from pathlib import Path
import tempfile
import unittest

from tools import check_qa08_native_hdma_setini_source as probe

COLOURS=[
    (0,"2086","2F"),(2,"2086","2F"),
    (3,"2089","40"),(4,"208C","80"),
    (113,"208F","20"),(114,"2092","53"),(115,"2095","80"),
]
SETINI=["01","01","6D","01","01","6D","00"]

def reports(root:Path):
    colour={
        "schema":"qa08-native-HDMA-COLDATA-original-source-provenance/1",
        "guest_frame":2208,
        "direct_native_HDMA_COLDATA_written_bytes":7,
        "HDMA_channels_recorded":{"5":7},
        "records":[{
            "A_bus_source":"7E:"+address,
            "COLDATA_written_byte":"0x"+value,
            "reported_native_journal_frame":2208,
            "journal_scanline_tag":tag,
            "HDMA_channel":5,
            "DMA_mode":1,
            "HDMA_indirect":False,
            "PPU_register":"$2132",
        } for tag,address,value in COLOURS]
    }
    txt={
        "guest_frame":2208,
        "native_compositor_pixel_records":78,
        "guest_CRC_entries_equal":2473,
        "stock_native_BG3_main_OBJ_subscreen":26,
        "front_removed_native_empty_subscreen":26,
    }
    cp,tp=root/"colour.json",root/"text.json"
    cp.write_text(json.dumps(colour))
    tp.write_text(json.dumps(txt))
    return cp,tp

def log_lines():
    lines=[]
    for (tag,address,_),value in zip(COLOURS,SETINI):
        src=int(address,16)+1
        line=(f"UR_QA08_HDMA_SETINI frame=2208 tagframe=2208 line={tag} "
              f"channel=5 bbus=33 value={value} src=7E:{src:04X} "
              f"mode=1 indirect=0 table={src+1:04X} bank=7E setini={value}")
        lines.append(line)
    return lines

class OriginalSetiniTests(unittest.TestCase):
    def test_strict_actual_2133_pairs_AND_accepted_original_bg3(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            cp,tp=reports(root)
            lp=root/"log.txt"
            lp.write_text("\n".join(log_lines())+"\n")
            result=probe.check(lp,cp,tp)
            self.assertEqual(result["observed_native_SETINI_companion_records"],7)
            self.assertEqual(result["original_executed_2P_WRAM_source_values_observed"],5)
            self.assertEqual(result["original_executed_2P_WRAM_source_comparison_matches"],6)
            self.assertEqual(result["samples"][-1]["original_Snes9x_observed_WRAM_value"],None)
            self.assertFalse(result["full_original_native_same_input_parity_proven"])
            self.assertFalse(result["physical_SNES_hardware_timing_proven"])

    def test_malformed_and_missing_native_setini_records_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cp,tp=reports(root);lp=root/"log.txt"
            ls=log_lines()
            lp.write_text("\n".join(ls[:-1])+"\n")
            with self.assertRaisesRegex(ValueError,"seven"):
                probe.check(lp,cp,tp)
            lp.write_text("\n".join(ls)+"\nUR_QA08_HDMA_SETINI_OVERFLOW frame=2208 limit=2048\n")
            with self.assertRaisesRegex(ValueError,"overflow"):
                probe.check(lp,cp,tp)
            for old,new in [("bbus=33","bbus=32"),("setini=01","setini=02"),
                            ("src=7E:2087","src=7E:2089"),
                            ("table=2088","table=2087"),
                            ("channel=5","channel=4"),
                            ("mode=1","mode=0")]:
                newlines=ls.copy()
                newlines[0]=newlines[0].replace(old,new)
                lp.write_text("\n".join(newlines)+"\n")
                with self.assertRaisesRegex(ValueError,"source|record"):
                    probe.check(lp,cp,tp)

    def test_native_parent_provenance_cannot_be_forged(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cp,tp=reports(root);lp=root/"log.txt"
            lp.write_text("\n".join(log_lines())+"\n")
            text=json.loads(tp.read_text())
            text["guest_CRC_entries_equal"]=2472
            tp.write_text(json.dumps(text))
            with self.assertRaisesRegex(ValueError,"source gate"):
                probe.check(lp,cp,tp)
            text["guest_CRC_entries_equal"]=2473
            tp.write_text(json.dumps(text))
            colour=json.loads(cp.read_text())
            colour["HDMA_channels_recorded"]={"4":7}
            cp.write_text(json.dumps(colour))
            with self.assertRaisesRegex(ValueError,"COLDATA"):
                probe.check(lp,cp,tp)


if __name__=="__main__":
    unittest.main()
