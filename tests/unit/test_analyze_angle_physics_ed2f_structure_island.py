import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_angle_physics_ed2f_structure_island as mod

class ED2FAnglePhysicsTests(unittest.TestCase):
 def test_partition(self):
  self.assertEqual(sum(mod.cpu_to_offset(e)-mod.cpu_to_offset(s)+1 for _,_,s,e in mod.REGIONS),904)
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROM corpus absent")
  r=mod.build()
  self.assertEqual(r["next_entry"],"83:F0B7")
  self.assertEqual(r["bounded_bytes"],904)
  self.assertEqual([x["size"] for x in r["regions"]],[4,477,423])
  self.assertEqual([x["callsite"] for x in r["accepted_caller_edges"]],["82:8C74","82:915E"])
  for x in r["regions"]:
   self.assertEqual(x["builds"]["usa-retail"]["unreached_or_data_bytes"],0,x["name"])
if __name__=="__main__": unittest.main()
