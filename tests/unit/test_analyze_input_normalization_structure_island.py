import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_input_normalization_structure_island as mod
class T(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["usa_start"],"82:AA6E")
  self.assertEqual(r["usa_end"],"82:ACA0")
  print("INPUT_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
