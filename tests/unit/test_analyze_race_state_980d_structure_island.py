import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_race_state_980d_structure_island as mod

class RaceState980DTests(unittest.TestCase):
 def test_partition(self):
  total=sum(mod.cpu_to_offset(e)-mod.cpu_to_offset(s)+1 for _,_,s,e in mod.REGIONS)
  self.assertEqual(total,mod.cpu_to_offset("82:98BD")-mod.cpu_to_offset("82:980D")+1)
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROM corpus absent")
  r=mod.build()
  self.assertEqual(r["next_entry"],"82:98BE")
  self.assertEqual(r["accepted_caller_edges"],[{"callsite":"83:CD59","kind":"JSL","source":"race-frame-orchestrator","region":"loop_body_after_sep_cleanup"}])
  self.assertEqual(r["bounded_bytes"],177)
  for region in r["regions"]:
   self.assertEqual(region["builds"]["usa-retail"]["unreached_or_data_bytes"],0,region["name"])
   for b in ("legacy-beta","pal-prototype-1994-11-29","europe-retail"):
    item=region["builds"][b]
    self.assertEqual(item["aligned_role_disagreements"],0,(region["name"],b))
    self.assertEqual(item["aligned_opcode_pairs"],item["aligned_equal_opcode_pairs"],(region["name"],b))
if __name__=="__main__": unittest.main()
