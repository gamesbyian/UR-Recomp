import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_accept", ROOT/"tools/analyze_widescreen_doublepass_acceptance.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

def desc(slot,dest,payload,source):
    return {
        "slot":slot,"ready":1,"vram":dest,"source":source,
        "size":0x20,"vmain":0x81,"payload_hex":payload,
    }

def row(frame,site,camx,descs):
    return {
        "frame":frame,"site":site,"camx":camx,"camy":10,"camdx":2,"camdy":0,
        "gameplay":{"px":1,"py":2,"xs":3,"ys":4,"pitch":5,"contact":6,
                    "laps":7,"checkpoint":8,"finish":9},
        "ready":descs,
        "descriptors":descs,
    }

class DoublepassAcceptanceTests(unittest.TestCase):
    def test_accepts_consecutive_adjacent_future_columns_with_post_nmi_bytes(self):
        control=[]
        wide=[]
        vram={}
        for f in range(20):
            payload=(f.to_bytes(2,"little")*16).hex().upper()
            primary=desc(2,0x0D80+(f%32),payload,0x0433)
            control += [row(f,"after_build",f,[primary]),row(f,"before_consume",f,[primary])]
            wdescs=[primary]
            if f<19:
                next_payload=((f+1).to_bytes(2,"little")*16).hex().upper()
                extra=desc(3,0x0D80+((f+1)%32),next_payload,0x0453)
                wdescs=[primary,extra]
                vram[f]={(3,extra["vram"]):next_payload,(2,primary["vram"]):payload}
            wide += [row(f,"after_build",f,wdescs),row(f,"before_consume",f,wdescs)]
        report=MOD.analyze(control,wide,vram)
        self.assertTrue(report["success"])
        self.assertGreaterEqual(report["longest_consecutive_acceptance_run"],8)

    def test_ring_next_generalizes_beyond_d80_page(self):
        self.assertEqual(MOD.ring_next(0x0D9F),0x0D80)
        self.assertEqual(MOD.ring_next(0x0DAE),0x0DAF)
        self.assertEqual(MOD.ring_next(0x0DBF),0x0DA0)

    def test_parse_vram(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.log"
            p.write_text(
                "WSVRAM frame=4 cols=2:0D80:"+"AA"*32+",3:0D81:"+"BB"*32+"\n"
                "noise\n"
                "WSVRAM frame=5 cols=2:0D81:"+"CC"*32+",3:0D82:"+"DD"*32+"\n"
            )
            parsed=MOD.parse_vram(p)
            self.assertEqual(parsed[4][(3,0x0D81)],"BB"*32)
            self.assertEqual(parsed[5][(3,0x0D82)],"DD"*32)

if __name__=="__main__":
    unittest.main()
