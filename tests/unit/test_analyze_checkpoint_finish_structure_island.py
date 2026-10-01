import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_checkpoint_finish_structure_island as mod
import build_comparative_structural_census as census_mod

class CheckpointFinishTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()):
   self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["dispatch"]["entry"],"81:8050")
  self.assertEqual(r["dispatch"]["object_code"],"0x14")
  self.assertEqual(r["usa_size"],657)
  self.assertEqual(sum(x["size"] for x in r["regions"]),657)
  self.assertEqual(r["lineage_edits"]["pal_line_total_contraction"],-29)
  self.assertEqual(r["lineage_edits"]["europe_total_contraction_after_both_lineages"],-43)
  deletions=r["lineage_edits"]["pal_line_usa_only_deletions"]
  self.assertEqual([x["size"] for x in deletions],[6,6,6,7,4])
  self.assertEqual(sum(x["size"] for x in deletions),29)
  for region in r["regions"]:
   usa=region["builds"]["usa-retail"]
   self.assertEqual(usa["unreached_or_data_bytes"],0,region["name"])
   beta=region["builds"].get("legacy-beta")
   if beta:
    self.assertEqual(beta["similarity"],1.0,region["name"])
  for d in deletions:
   self.assertEqual(d["hex"],d["expected_hex"],d["name"])
   self.assertTrue(d["legacy_beta_identical"],d["name"])
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("CHECKPOINT_FINISH_JSON="+json.dumps(r,sort_keys=True))

if __name__=="__main__":
 unittest.main()
