import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_course_resource_helper_structure_island as mod

class CourseResourceHelperTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["usa_start"],"82:B293")
  self.assertEqual(r["usa_end"],"82:B32E")
  self.assertEqual(r["next_data"],"82:B32F")
  self.assertEqual(sum(x["size"] for x in r["regions"]),156)
  self.assertEqual({x["callsite"] for x in r["known_callers"]},{"82:E18C","82:E1F5"})
  for region in r["regions"]:
   self.assertEqual(region["builds"]["legacy-beta"]["similarity"],1.0,region["name"])
   self.assertEqual(region["builds"]["usa-retail"]["unreached_or_data_bytes"],0,region["name"])
   for build in ("legacy-beta","pal-prototype-1994-11-29","europe-retail"):
    item=region["builds"][build]
    self.assertEqual(item["aligned_opcode_pairs"],item["aligned_equal_opcode_pairs"],(region["name"],build))
    self.assertEqual(item["aligned_role_disagreements"],0,(region["name"],build))
  print("COURSE_RESOURCE_HELPER_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
