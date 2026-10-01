import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_contact_geometry_structure_island as mod
class ContactGeometryTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["usa_start"],"81:9E2A")
  self.assertEqual(r["next_code_entry"],"81:9FBF")
  print("CONTACT_GEOMETRY_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
