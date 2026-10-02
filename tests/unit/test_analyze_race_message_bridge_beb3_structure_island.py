import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_race_message_bridge_beb3_structure_island as mod
import build_comparative_structural_census as census_mod

class RaceMessageBridgeTests(unittest.TestCase):
 def test_partition(self):
  total=sum(mod.cpu_to_offset(e)-mod.cpu_to_offset(s)+1 for _,_,s,e in mod.REGIONS)
  self.assertEqual(total,554)
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["next_entry"],"81:C0DD")
  self.assertEqual([x["size"] for x in r["regions"]],[4,138,162,250])
  for x in r["regions"]:
   self.assertEqual(x["builds"]["usa-retail"]["unreached_or_data_bytes"],0,x["name"])
   for build in ("legacy-beta","pal-prototype-1994-11-29","europe-retail"):
    item=x["builds"][build]
    self.assertEqual(item["aligned_role_disagreements"],0,(x["name"],build))
    self.assertEqual(item["aligned_opcode_pairs"],item["aligned_equal_opcode_pairs"],(x["name"],build))
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("RACE_MESSAGE_BEB3_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
