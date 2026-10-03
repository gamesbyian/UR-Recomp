import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "ws_reach", ROOT/"tools/analyze_native_widescreen_reachability.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class FakeDisasm:
    OP_CODE = 1
    def __init__(self, size, executable):
        self.code_map = bytearray(size)
        for off in executable:
            self.code_map[off] = self.OP_CODE

class NativeWidescreenReachabilityTests(unittest.TestCase):
    def test_filters_short_calls_by_bank_and_classifies_code(self):
        blob=bytearray(0x9000)
        # Same bytes in bank 80 are not a call to bank-81 A52F.
        blob[1:4]=bytes.fromhex("20 2F A5")
        # This one is in LoROM bank 81 and is a legitimate short-call candidate.
        blob[0x8001:0x8004]=bytes.fromhex("20 2F A5")
        # Long call is explicit-bank and remains valid from bank 80.
        blob[8:12]=bytes.fromhex("22 2F A5 81")
        d=FakeDisasm(len(blob), {8,0x8001})
        refs=MOD._classify_refs(bytes(blob),"81:A52F",d)
        self.assertEqual([r["file_offset"] for r in refs["jsr"]],[0x8001])
        self.assertTrue(refs["jsr"][0]["executable"])
        self.assertEqual([r["file_offset"] for r in refs["jsl"]],[8])
        self.assertTrue(refs["jsl"][0]["executable"])

if __name__=="__main__":
    unittest.main()
