import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_collision_response_structure_island as mod
class CollisionResponseTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["usa_start"],"81:8FB8")
  self.assertEqual(r["next_code_entry"],"81:99D6")
  print("COLLISION_RESPONSE_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
