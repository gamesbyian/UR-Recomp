import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_secondary", ROOT/"tools/analyze_widescreen_secondary_lane.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class SecondaryLaneAnalyzerTests(unittest.TestCase):
    def test_signature_uses_destination_size_mode_and_payload(self):
        d={"vram":0x0D80,"size":0x20,"vmain":0x81,"payload_hex":"AA"*32}
        self.assertEqual(MOD.sig(d),(0x0D80,0x20,0x81,"AA"*32))

if __name__=="__main__":
    unittest.main()
