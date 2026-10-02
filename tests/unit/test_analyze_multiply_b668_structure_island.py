import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_multiply_b668_structure_island as mod

class MultiplyB668Tests(unittest.TestCase):
 def test_partition(self):
  self.assertEqual(mod.cpu_to_offset("81:B68A")-mod.cpu_to_offset("81:B664")+1,39)
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROM corpus absent")
  r=mod.build()
  self.assertEqual(r["next_entry"],"81:B68B")
  self.assertEqual(r["bounded_bytes"],39)
  self.assertEqual(r["accepted_caller_edges"],[{"callsite":"81:A511","kind":"JSR","source":"camera-control","region":"camera_scale_config"}])
  for region in r["regions"]:
   self.assertEqual(region["builds"]["usa-retail"]["unreached_or_data_bytes"],0,region["name"])
   for b in ("legacy-beta","pal-prototype-1994-11-29","europe-retail"):
    item=region["builds"][b]
    self.assertEqual(item["aligned_role_disagreements"],0,(region["name"],b))
    self.assertEqual(item["aligned_opcode_pairs"],item["aligned_equal_opcode_pairs"],(region["name"],b))
if __name__=="__main__": unittest.main()
