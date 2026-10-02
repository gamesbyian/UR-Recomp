import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_race_loop_e7a5_structure_island as mod
import build_comparative_structural_census as census_mod

class RaceLoopE7A5Tests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build(); x=r["regions"][0]
  self.assertEqual(r["usa_start"],"83:E7A5")
  self.assertEqual(r["usa_end"],"83:EBCB")
  self.assertEqual(r["next_entry"],"83:EBCC")
  self.assertEqual(x["size"],1063)
  self.assertEqual(x["builds"]["legacy-beta"]["size"],1063)
  self.assertEqual(x["builds"]["pal-prototype-1994-11-29"]["size"],1109)
  self.assertEqual(x["builds"]["europe-retail"]["size"],1107)
  self.assertEqual(x["builds"]["pal-prototype-1994-11-29"]["shift_start"],-10)
  self.assertEqual(x["builds"]["pal-prototype-1994-11-29"]["shift_end"],36)
  self.assertEqual(x["builds"]["europe-retail"]["shift_start"],28)
  self.assertEqual(x["builds"]["europe-retail"]["shift_end"],72)
  for build in mod.ROMS:
   self.assertEqual(x["builds"][build]["unreached_or_data_bytes"],0,build)
  self.assertEqual(x["builds"]["legacy-beta"]["similarity"],1.0)
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("RACE_LOOP_E7A5_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
