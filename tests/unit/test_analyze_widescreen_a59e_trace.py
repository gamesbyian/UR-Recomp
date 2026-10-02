import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_a59e", ROOT/"tools/analyze_widescreen_a59e_trace.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class A59ETraceTests(unittest.TestCase):
    def test_absent_payload_write_is_retained_negative_evidence(self):
        rows=[
            {"frame":1,"pc":0x81A5B1,"op":0x20,"b1":0x59,"b2":0xAE,
             "a":0,"x":0,"y":0,"d":0,"p":0,
             "e0505":0xFFFF,"e0521":0x181,"c052b":0,
             "payload":"00"*32},
            {"frame":1,"pc":0x81A5B4,"op":0x80,"b1":0x09,"b2":0xA9,
             "a":0,"x":0,"y":0,"d":0,"p":0,
             "e0505":0x182,"e0521":0x182,"c052b":0x10,
             "payload":"00"*32},
        ]
        report=MOD.analyze(rows)
        self.assertEqual(report["classification"],"payload-not-staged-before-ab88")
        self.assertIsNone(report["stable_payload_site"])
        self.assertEqual(report["stable_edge_site"]["from_pc"],0x81A5B1)

if __name__=="__main__":
    unittest.main()
