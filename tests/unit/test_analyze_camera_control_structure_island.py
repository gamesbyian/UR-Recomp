import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_camera_control_structure_island as mod
class CameraControlTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["per_frame_entry"],"81:A52F")
  print("CAMERA_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
