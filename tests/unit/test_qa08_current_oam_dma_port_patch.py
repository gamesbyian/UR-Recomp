"""No renderer edits: pinned current-result OAM input port trace and positive 544-byte decode."""
import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tools")]
from tools import qa08_current_result_oam_port_patch as o
from tools import qa08_current_result_cgram_port_patch as c
from tools import qa08_current_result_source_witness as w

class TestPortWitness(unittest.TestCase):
    def test_pinned_port_patch_and_tamper_refusal(self):
        raw='#include <stdio.h>\n#include <stdlib.h>\n'+c.ANCHOR+c.TRACE+(
            'case OAMADDL & 0xff: ;\ncase OAMADDH & 0xff: ;\ncase 0x04: { ;\n')
        src=o.patch_source(raw)
        self.assertEqual(o.patch_source(src),src)
        self.assertIn("UR_QA08_WIN_OAM_PORT frame=",src)
        self.assertIn("snes_frame_counter >= 4173",src)
        for bad in (raw.replace("case 0x04: {",""),src.replace("oldlow=%02x","oldlow=%04x"),
                    src.replace(o.MARK,"INVALID_OBSERVER_MARK")):
            with self.assertRaises(ValueError):o.patch_source(bad)
    def test_incoming_full_dma_real_latch_order_required(self):
        def event(f,i):
            high=int(i>=512)
            adr=(i//2)&255 if i<512 else ((i-512)//2)&15
            return (f"UR_QA08_WIN_OAM_PORT frame={f} v=226 h=100 port=04 "
                    f"val={i&255:02x} src=1 adr={adr:02x} high={high} "
                    f"second={i%2} latch=00 oldlow=00 oldhigh=00")
        a=[event(4030,i) for i in range(544)]
        b=[event(4174,i) for i in range(544)]
        result=w.inspect_current_oam_dma("\n".join(a+b))
        self.assertEqual(len(result["full_544byte_DMA_transfers"]),2)
        self.assertEqual(result["all_real_oam_port_events"],1088)
        with self.assertRaises(ValueError):
            w.inspect_current_oam_dma("\n".join(a[1:]+b))
        with self.assertRaises(ValueError):
            w.inspect_current_oam_dma("")
if __name__=="__main__":unittest.main()
