import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_course_sector_gather_structure_island as mod

class CourseSectorGatherTests(unittest.TestCase):
 def test_boundary(self):
  self.assertEqual(mod.cpu_to_offset(mod.END)-mod.cpu_to_offset(mod.START)+1,331)
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROM corpus absent")
  r=mod.build()
  self.assertEqual(r["next_region"],"81:8B95")
  self.assertEqual(r["builds"]["legacy-beta"]["similarity"],1.0)
  self.assertEqual(r["builds"]["usa-retail"]["unreached_or_data_bytes"],0)
  for name in ("pal-prototype-1994-11-29","europe-retail","legacy-beta"):
   b=r["builds"][name]
   self.assertEqual(b["aligned_role_disagreements"],0,name)
   self.assertEqual(b["aligned_opcode_pairs"],b["aligned_equal_opcode_pairs"],name)
if __name__=="__main__": unittest.main()
