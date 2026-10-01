import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_player_state_marshal_structure_island as mod
class PlayerStateMarshalTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["long_entry"],"81:8D14")
  self.assertEqual(r["next_code_entry"],"81:8FB8")
  print("PLAYER_STATE_MARSHAL_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
