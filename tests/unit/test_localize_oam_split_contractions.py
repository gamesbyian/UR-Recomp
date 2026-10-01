import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import localize_oam_split_contractions as mod

class OamSplitContractionTests(unittest.TestCase):
    def test_rom_backed_contractions_when_roms_present(self):
        if not all(path.exists() for path in mod.ROMS.values()):
            self.skipTest("preserved ROM corpus not present")
        result=mod.build()
        self.assertEqual(len(result["regions"]),2)
        for region in result["regions"]:
            for build in ("pal-prototype-1994-11-29","europe-retail"):
                self.assertEqual(region["builds"][build]["net_size_delta"],-2)
        print("OAM_CONTRACTION_JSON="+json.dumps(result,sort_keys=True))

if __name__=="__main__":
    unittest.main()
