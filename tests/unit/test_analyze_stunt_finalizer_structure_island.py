import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_stunt_finalizer_structure_island as mod
import build_comparative_structural_census as census_mod

class StuntFinalizerTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()):
   self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["routine_end"],"82:9D8B")
  self.assertEqual(r["next_code_entries"]["usa-retail"],"82:A01B")
  self.assertEqual(r["next_code_entries"]["pal-prototype-1994-11-29"],"82:A011")
  self.assertEqual(r["next_code_entries"]["europe-retail"],"82:A027")
  self.assertEqual(r["lineage_edit"]["hex"],"ea ea ea ea ea")
  self.assertEqual(sum(x["size"] for x in r["regions"]),1497)
  for region in r["regions"]:
   usa=region["builds"]["usa-retail"]
   beta=region["builds"]["legacy-beta"]
   self.assertEqual(beta["similarity"],1.0,region["name"])
   if region["kind"]=="code":
    self.assertEqual(usa["unreached_or_data_bytes"],0,region["name"])
    for build in ("pal-prototype-1994-11-29","europe-retail"):
     q=region["builds"].get(build)
     if q: self.assertEqual(q["unreached_or_data_bytes"],0,(region["name"],build))
  for name in ("flip_score_weights","roll_score_weights","twist_score_weights","trick_praise_table"):
   region=next(x for x in r["regions"] if x["name"]==name)
   for build in region["builds"].values():
    self.assertEqual(build["similarity"],1.0,(name,build["start"]))
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("STUNT_ISLAND_JSON="+json.dumps(r,sort_keys=True))

if __name__=="__main__": unittest.main()
