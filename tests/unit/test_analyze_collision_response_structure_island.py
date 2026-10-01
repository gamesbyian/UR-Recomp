import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_collision_response_structure_island as mod
import build_comparative_structural_census as census_mod
class CollisionResponseTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["usa_start"],"81:8FB8")
  self.assertEqual(r["next_code_entry"],"81:99D6")
  self.assertEqual(sum(x["size"] for x in r["regions"]),2590)
  self.assertEqual([x["size"] for x in r["europe_only_insertions"]],[6,11])
  self.assertEqual(sum(x["size"] for x in r["dormant_usa_code"]),53)
  self.assertEqual(r["usa_unreached_runs"],[
   {"start":"81:9484","end":"81:948A","size":7},
   {"start":"81:9646","end":"81:9669","size":36},
   {"start":"81:96AD","end":"81:96AF","size":3},
   {"start":"81:9972","end":"81:9978","size":7},
  ])
  for region in r["regions"]:
   self.assertEqual(region["builds"]["legacy-beta"]["similarity"],1.0,region["name"])
   for build in ("pal-prototype-1994-11-29","europe-retail"):
    q=region["builds"][build]
    self.assertEqual(q["aligned_opcode_consensus_fraction"],1.0,(region["name"],build))
    self.assertEqual(q["aligned_role_disagreements"],0,(region["name"],build))
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("COLLISION_RESPONSE_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
