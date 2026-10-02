import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_race_loop_e580_control_structure_island as mod

class E580IslandTests(unittest.TestCase):
 def test_partition(self):
  self.assertEqual(mod.cpu_to_offset("83:E57F")-mod.cpu_to_offset("83:E540")+1,64)
  self.assertEqual(mod.cpu_to_offset("83:E7A4")-mod.cpu_to_offset("83:E580")+1,549)
  total=sum(mod.cpu_to_offset(e)-mod.cpu_to_offset(s)+1 for _,_,s,e in mod.REGIONS)
  self.assertEqual(total,613)
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROM corpus absent")
  r=mod.build()
  self.assertEqual(r["next_entry"],"83:E7A5")
  self.assertEqual(r["accepted_caller_edges"],[{"callsite":"83:CD47","kind":"JSR","source":"race-frame-orchestrator","region":"loop_body_after_sep_cleanup"}])
  self.assertEqual(r["regions"][0]["kind"],"data")
  self.assertEqual(r["regions"][1]["builds"]["usa-retail"]["unreached_or_data_bytes"],0)
  for b in ("legacy-beta","pal-prototype-1994-11-29","europe-retail"):
   item=r["regions"][1]["builds"][b]
   self.assertEqual(item["aligned_role_disagreements"],0,b)
   self.assertEqual(item["aligned_opcode_pairs"],item["aligned_equal_opcode_pairs"],b)
if __name__=="__main__": unittest.main()
