import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import analyze_race_frame_orchestrator_structure_island as mod

class RaceFrameOrchestratorTests(unittest.TestCase):
    def test_bounds_include_loop(self):
        self.assertEqual(mod.USA_START,"83:CBCC")
        self.assertEqual(mod.USA_END,"83:CD9F")
        self.assertEqual(mod.cpu_to_offset(mod.USA_END)-mod.cpu_to_offset(mod.USA_START)+1,468)

    def test_rom_backed_probe_when_roms_present(self):
        if not all(path.exists() for path in mod.ROMS.values()):
            self.skipTest("preserved ROM corpus not present")
        r=mod.build()
        self.assertEqual(r["usa_size"],468)
        self.assertEqual(r["builds"]["usa-retail"]["unreached_or_data_bytes"],0)
        self.assertEqual(r["builds"]["legacy-beta"]["similarity"],1.0)
        self.assertIn("83:CC62",r["builds"]["usa-retail"]["opcode_starts"])
        self.assertIn("83:CD9D",r["builds"]["usa-retail"]["opcode_starts"])
        self.assertEqual(set(r["builds"]), set(mod.ROMS))
        for build, info in r["builds"].items():
            self.assertEqual(info["size"], 468, build)
            self.assertEqual(info["size_delta"], 0, build)
        print("RACE_FRAME_ORCHESTRATOR_JSON="+json.dumps(r,sort_keys=True))

if __name__=="__main__":
    unittest.main()
