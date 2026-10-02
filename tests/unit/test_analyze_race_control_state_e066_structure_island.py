import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_race_control_state_e066_structure_island as mod
import build_comparative_structural_census as census_mod

class RaceControlStateE066Tests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["usa_start"],"83:E066")
  self.assertEqual(r["usa_end"],"83:E53F")
  self.assertEqual(r["next_entry"],"83:E540")
  self.assertEqual([x["size"] for x in r["regions"]],[466,776])
  self.assertEqual(len(r["known_callers"]),2)
  for x in r["regions"]:
   self.assertEqual(x["builds"]["usa-retail"]["unreached_or_data_bytes"],0,x["name"])
   self.assertEqual(x["builds"]["legacy-beta"]["similarity"],1.0,x["name"])
   for build in ("legacy-beta","pal-prototype-1994-11-29","europe-retail"):
    item=x["builds"][build]
    self.assertEqual(item["aligned_opcode_pairs"],item["aligned_equal_opcode_pairs"],(x["name"],build))
    self.assertEqual(item["aligned_role_disagreements"],0,(x["name"],build))
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("RACE_CONTROL_E066_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
