import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "progression_acceptance", ROOT/"tools/analyze_progression_sram_acceptance.py")
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class ProgressionAcceptanceTests(unittest.TestCase):
    def test_checksum_matches_known_word_sum_shape(self):
        data=bytearray(8192)
        for i in range(MOD.CHECKSUM_WORDS):
            data[MOD.CHECKSUM_START+i*2:MOD.CHECKSUM_START+i*2+2]=(i+1).to_bytes(2,"little")
        self.assertEqual(MOD.checksum(data), sum(range(1,MOD.CHECKSUM_WORDS+1)) & 0xFFFF)

    def test_region_changes_reports_exact_offsets(self):
        a=bytearray(8192); b=bytearray(a)
        b[MOD.MEDAL_START]=1
        b[MOD.MEDAL_START+17]=2
        self.assertEqual(
            MOD.region_changes(a,b,MOD.MEDAL_START,MOD.MEDAL_END),
            [
                {"offset":MOD.MEDAL_START,"before":0,"after":1},
                {"offset":MOD.MEDAL_START+17,"before":0,"after":2},
            ],
        )

if __name__=="__main__":
    unittest.main()
