import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_race_timer_structure_island as mod
class TimerIslandTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["long_entry"],"81:C697")
  self.assertEqual(r["countdown_entry"],"81:C7E1")
  print("TIMER_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
