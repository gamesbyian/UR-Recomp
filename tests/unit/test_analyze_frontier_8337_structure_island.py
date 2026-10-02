import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_frontier_8337_structure_island as mod

class Frontier8337Tests(unittest.TestCase):
 def test_partition(self):
  total=sum(mod.cpu_to_offset(e)-mod.cpu_to_offset(s)+1 for _,_,s,e in mod.REGIONS)
  self.assertEqual(total+3,mod.cpu_to_offset("82:8951")-mod.cpu_to_offset("82:8337")+1)
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROM corpus absent")
  r=mod.build()
  print("FRONTIER_8337_JSON="+json.dumps(r,sort_keys=True))
  self.assertEqual(r["bounded_bytes"],1563)
  self.assertEqual(r["homolog_region_bytes"],1560)
  self.assertEqual(r["next_entry"],"82:8952")
  self.assertEqual(r["accepted_caller_edges"],[{"callsite":"83:CD82","source":"race-frame-orchestrator","region":"loop_body_after_sep_cleanup","kind":"JSL"}])
  self.assertEqual(r["regions"][1]["kind"],"data")
  self.assertEqual(r["regions"][1]["size"],50)
  self.assertEqual(r["lineage_edits"][0]["usa_span"],"82:853D..853F")
  self.assertEqual(r["lineage_edits"][0]["instruction"],"JSR $892A")
  for region in r["regions"]:
   if region["kind"]=="code":
    self.assertEqual(region["builds"]["usa-retail"]["unreached_or_data_bytes"],0,region["name"])
    for build in ("legacy-beta","pal-prototype-1994-11-29","europe-retail"):
     item=region["builds"][build]
     self.assertEqual(item["aligned_role_disagreements"],0,(region["name"],build))
     self.assertEqual(item["aligned_opcode_pairs"],item["aligned_equal_opcode_pairs"],(region["name"],build))
if __name__=="__main__": unittest.main()
