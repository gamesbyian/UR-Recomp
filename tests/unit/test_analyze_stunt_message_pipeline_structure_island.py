import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_stunt_message_pipeline_structure_island as mod
import build_comparative_structural_census as census_mod
class T(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["usa_start"],"81:C0DD")
  self.assertEqual(r["usa_end"],"81:C604")
  self.assertEqual(sum(x["size"] for x in r["regions"]),1320)
  self.assertEqual(r["next_code_entry"],"81:C605")
  self.assertEqual(r["lineage_edits"]["pal_line_nop_cleanup"]["hex"],"ea ea ea")
  self.assertEqual(r["lineage_edits"]["europe_two_player_gate"]["europe_span"],"81:C360..C367")
  data=next(x for x in r["regions"] if x["name"]=="message_reward_lookup_block")
  for build in data["builds"].values():
   self.assertEqual(build["similarity"],1.0)
  for region in r["regions"]:
   usa=region["builds"]["usa-retail"]
   self.assertEqual(region["builds"]["legacy-beta"]["similarity"],1.0,region["name"])
   if region["kind"]=="code":
    self.assertEqual(usa["unreached_or_data_bytes"],0,region["name"])
    for build in ("pal-prototype-1994-11-29","europe-retail"):
     q=region["builds"].get(build)
     if q: self.assertEqual(q["unreached_or_data_bytes"],0,(region["name"],build))
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("STUNT_MESSAGE_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
