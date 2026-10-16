"""Native OAM ports: source-qualified, opt-in, no guest or renderer changes."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_qa08_native_inidisp_port_trace_patch as prev
import baldosa_qa08_native_oam_port_chronology_patch as stage
import qa08_windows_native_oam_port_chronology as verify

class OamSourceObserver(unittest.TestCase):
    def setUp(self):
        self.base=("#include <stdio.h>\n#include <stdlib.h>\n"+
            prev.ANCHOR+prev.TRACE+"  switch(adr) {\n"
            "case OAMADDL & 0xff: break;\n"
            "case OAMADDH & 0xff: break;\n"
            "case 0x04: {break;}\n}\n"+prev.MARK+"\n")

    def test_instrumentation_never_changes_original_port_handler(self):
        next=stage.patch_source(self.base)
        self.assertEqual(stage.patch_source(next),next)
        self.assertEqual(next.count(stage.MARK),1)
        self.assertEqual(next.count("ppu_wlog_note(adr, val);"),1)
        self.assertIn("g_ppu_wlog_src",next)
        self.assertIn("UR_QA08_WINDOWS_OAM_PORT_TRACE",next)
        self.assertIn("snes_frame_counter >= 4029",next)
        self.assertIn("snes_frame_counter <= 4178",next)
        self.assertEqual(next.replace(stage.ANCHOR+stage.TRACE,stage.ANCHOR),self.base)

    def test_bad_pins_or_missing_previous_trace_refuse_stage(self):
        for bad in (self.base.replace(prev.TRACE,""),
                    self.base.replace("case 0x04: {break;}",""),
                    self.base+self.base,
                    stage.patch_source(self.base).replace("UR_QA08_NATIVE_OAM_PORT_BEFORE_WRITE:","tampered:")):
            with self.subTest(part=bad[:60]),self.assertRaises(ValueError):
                stage.patch_source(bad)

class PortInputConservation(unittest.TestCase):
    def setUp(self):
        self.receipt={"real_native_2p_guest_frames":5484,
          "real_native_2p_guest_crc_sha256":verify.CRC,
          "independently_source_qualified_native_scanline_OAM_snapshots":70}
        self.lines=[]
        for frame in (4031,4175):
            for i in range(544):
                adr=(i//2)%(16 if i>=512 else 256)
                hi=int(i>=512)
                self.lines.append(
                  f"UR_QA08_WIN_OAM_PORT frame={frame} v={226+i//220} "
                  f"h={i%220} port=04 val={i%256:02x} src=1 "
                  f"adr={adr:02x} high={hi} second={i%2} latch=00 "
                  f"oldlow=00 oldhigh=00")

    def test_complete_544_bytes_and_seven_source_tiles(self):
        d=verify.analyze("\n".join(self.lines),self.receipt)
        self.assertEqual(d["events_observed"],1088)
        self.assertEqual(len(d["frame_observations"]),2)
        for row in d["frame_observations"]:
            p=row["complete_sequential_zero_address_544byte_DMA"]
            self.assertTrue(p["complete_native_OAM_DMA_544_bytes"])
            self.assertEqual(p["native_DMA_source_slot_tile_bytes"]["112"],"c2")
            self.assertEqual(p["native_DMA_source_slot_tile_bytes"]["96"],"82")
            self.assertFalse(d["CPU_guest_WRAM_source_memory_proven"])
            self.assertFalse(d["release_approved"])

    def test_incomplete_source_DMA_must_not_be_invented(self):
        lines=self.lines[:-1]
        d=verify.analyze("\n".join(lines),self.receipt)
        self.assertIsNone(d["frame_observations"][-1]["complete_sequential_zero_address_544byte_DMA"])
        bad=self.lines.copy()
        bad[10]=bad[10].replace("src=1","src=3")
        d=verify.analyze("\n".join(bad),self.receipt)
        self.assertIsNone(d["frame_observations"][0]["complete_sequential_zero_address_544byte_DMA"])

    def test_reject_forged_guest_CRC_and_malformed_port(self):
        with self.assertRaises(ValueError):
            verify.analyze("\n".join(self.lines),{"real_native_2p_guest_frames":5484})
        with self.assertRaises(ValueError):
            verify.analyze("\n".join(self.lines).replace("port=04","port=08",1),self.receipt)
        with self.assertRaises(ValueError):
            verify.analyze("\n".join(self.lines).replace("frame=4031","frame=100",1),self.receipt)
        self.assertEqual(set(verify.SOURCE_ENUM),{0,1,2,3})

if __name__=="__main__":
    unittest.main()
