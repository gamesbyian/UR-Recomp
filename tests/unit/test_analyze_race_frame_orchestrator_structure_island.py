import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import analyze_race_frame_orchestrator_structure_island as mod

class RaceFrameOrchestratorTests(unittest.TestCase):
    def test_bounds_include_loop(self):
        self.assertEqual(mod.cpu_to_offset("83:CD9F")-mod.cpu_to_offset("83:CBCC")+1,468)

    def test_rom_backed_probe_when_roms_present(self):
        if not all(path.exists() for path in mod.ROMS.values()):
            self.skipTest("preserved ROM corpus not present")
        r=mod.build()
        self.assertEqual(r["usa_size"],468)
        self.assertTrue(r["loop"]["header_reached"])
        self.assertTrue(r["loop"]["back_edge_reached"])
        self.assertEqual(len(r["regions"]),2)
        first, second=r["regions"]
        self.assertEqual(first["usa_start"],"83:CBCC")
        self.assertEqual(first["usa_end"],"83:CC86")
        self.assertEqual(second["usa_start"],"83:CC87")
        self.assertEqual(second["usa_end"],"83:CD9F")
        for region in r["regions"]:
            self.assertEqual(region["builds"]["usa-retail"]["unreached_or_data_bytes"],0)
            self.assertEqual(region["builds"]["legacy-beta"]["similarity"],1.0)
        for build in mod.PAL_LINE_BUILDS:
            self.assertEqual(first["builds"][build]["size_delta"],-2)
        self.assertEqual(second["builds"]["pal-prototype-1994-11-29"]["shift"],-2)
        self.assertEqual(second["builds"]["europe-retail"]["shift"],36)
        self.assertEqual(r["lineage_edits"][0]["usa_span"],"83:CC85..CC86")
        print("RACE_FRAME_ORCHESTRATOR_JSON="+json.dumps(r,sort_keys=True))

if __name__=="__main__":
    unittest.main()
