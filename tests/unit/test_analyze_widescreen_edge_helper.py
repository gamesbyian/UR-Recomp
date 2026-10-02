import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_edge", ROOT/"tools/analyze_widescreen_edge_helper.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class WidescreenEdgeHelperTests(unittest.TestCase):
    def test_parse_changes(self):
        self.assertEqual(
            MOD.parse_changes("0505:9A:9B,052B:10:0F"),
            {0x0505:(0x9A,0x9B),0x052B:(0x10,0x0F)},
        )

    def test_instruction_rows_decodes_jsr_target(self):
        rows=[{
            "frame":1188,"pc":0x81A597,"op":0x20,"b1":0x34,"b2":0xA6,
            "a":0,"x":0xff,"y":0x10,"camx":1000,"camy":700,
            "edgex":400,"edgex2":0xffff,"edgey":0xffff,"edgey2":0xffff,
            "c0":16,"c1":0,"c2":0,"c3":0,
        }]
        decoded=MOD.instruction_rows(rows)
        self.assertEqual(decoded[0]["jsr_target"],0x81A634)
        self.assertEqual(decoded[0]["jsr_target_hex"],"81:A634")

if __name__=="__main__":
    unittest.main()
