import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "ws_reach", ROOT/"tools/analyze_native_widescreen_reachability.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class NativeWidescreenReachabilityTests(unittest.TestCase):
    def test_reports_short_and_long_refs(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"rom.sfc"
            blob=bytearray(64)
            blob[1:4]=bytes.fromhex("20 2F A5")
            blob[8:12]=bytes.fromhex("22 2B A5 81")
            p.write_bytes(blob)
            r=MOD.report(p)
            self.assertEqual(len(r["targets"]["per_frame_entry"]["jsr"]),1)
            self.assertEqual(len(r["targets"]["long_wrapper"]["jsl"]),1)
            self.assertEqual(r["direct_reference_count"],2)

if __name__=="__main__":
    unittest.main()
