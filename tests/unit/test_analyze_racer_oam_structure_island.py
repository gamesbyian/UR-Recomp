import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import analyze_racer_oam_structure_island as mod

class RacerOamStructureTests(unittest.TestCase):
    def test_partition_covers_named_routine(self):
        self.assertEqual(mod.REGIONS[0][1], "82:ACA5")
        self.assertEqual(mod.REGIONS[-1][2], "82:B17F")
        for (_,_,_,kind) in mod.REGIONS:
            self.assertEqual(kind, "code")

    def test_rom_backed_oam_island_when_roms_present(self):
        if not all(path.exists() for path in mod.ROMS.values()):
            self.skipTest("preserved ROM corpus not present")
        result=mod.build()
        self.assertEqual(len(result["regions"]), 12)
        by_name={r["name"]:r for r in result["regions"]}
        for region in result["regions"]:
            self.assertGreater(region["builds"]["usa-retail"]["opcode_bytes"], 0)
            self.assertEqual(region["builds"]["legacy-beta"]["similarity"], 1.0)
        for name in ("p1_projection","p2_projection_shared_camera"):
            self.assertEqual(by_name[name]["builds"]["europe-retail"]["shift"], 7)
            self.assertEqual(by_name[name]["builds"]["pal-prototype-1994-11-29"]["shift"], -15)
        for name in ("split_p2_projection","split_p1_projection"):
            self.assertEqual(by_name[name]["builds"]["europe-retail"]["size_delta"], -2)
            self.assertEqual(by_name[name]["builds"]["pal-prototype-1994-11-29"]["size_delta"], -2)
        self.assertEqual([x["usa_span"] for x in result["lineage_edits"]], ["82:AF96..AF97","82:B01F..B020"])
        print("RACER_OAM_ISLAND_JSON="+json.dumps(result,sort_keys=True))

if __name__=="__main__":
    unittest.main()
