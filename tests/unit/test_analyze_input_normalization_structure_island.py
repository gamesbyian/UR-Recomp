import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_input_normalization_structure_island as mod
import build_comparative_structural_census as census_mod
class T(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["usa_start"],"82:AA6E")
  self.assertEqual(r["usa_end"],"82:ACA0")
  self.assertEqual(sum(x["size"] for x in r["regions"]),563)
  for region in r["regions"]:
   self.assertEqual(region["builds"]["legacy-beta"]["similarity"],1.0,region["name"])
   for build in ("usa-retail","legacy-beta","pal-prototype-1994-11-29","europe-retail"):
    self.assertEqual(region["builds"][build]["unreached_or_data_bytes"],0,(region["name"],build))
  for build in ("pal-prototype-1994-11-29","europe-retail"):
   for item in r["opcode_consensus"][build].values():
    self.assertEqual(item["opcode_consensus_fraction"],1.0)
    self.assertEqual(item["role_disagreements"],0)
    self.assertEqual(item["mx_disagreements"],0)
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("INPUT_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
