import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_contact_geometry_structure_island as mod
import build_comparative_structural_census as census_mod
class ContactGeometryTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["usa_start"],"81:9E2A")
  self.assertEqual(r["next_code_entry"],"81:9FBF")
  self.assertEqual(sum(x["size"] for x in r["regions"]),405)
  self.assertEqual(sum(x["builds"]["usa-retail"]["opcode_bytes"] for x in r["regions"]),246)
  for region in r["regions"]:
   self.assertEqual(region["builds"]["usa-retail"]["unreached_or_data_bytes"],0,region["name"])
   self.assertEqual(region["builds"]["legacy-beta"]["similarity"],1.0,region["name"])
   self.assertEqual(region["builds"]["pal-prototype-1994-11-29"]["shift"],-32,region["name"])
   self.assertEqual(region["builds"]["europe-retail"]["shift"],-15,region["name"])
   for build in ("pal-prototype-1994-11-29","europe-retail"):
    item=region["builds"][build]
    self.assertEqual(item["aligned_opcode_pairs"],item["aligned_equal_opcode_pairs"],(region["name"],build))
    self.assertEqual(item["aligned_role_disagreements"],0,(region["name"],build))
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("CONTACT_GEOMETRY_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
