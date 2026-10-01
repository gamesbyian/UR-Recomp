import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"tools"))
import analyze_camera_control_structure_island as mod
import build_comparative_structural_census as census_mod
class CameraControlTests(unittest.TestCase):
 def test_rom_probe(self):
  if not all(p.exists() for p in mod.ROMS.values()): self.skipTest("ROMs absent")
  r=mod.build()
  self.assertEqual(r["per_frame_entry"],"81:A52F")
  self.assertEqual(sum(x["size"] for x in r["regions"]),1503)
  for region in r["regions"]:
   self.assertEqual(region["builds"]["legacy-beta"]["similarity"],1.0,region["name"])
   for build in ("usa-retail","legacy-beta","pal-prototype-1994-11-29","europe-retail"):
    self.assertEqual(region["builds"][build]["unreached_or_data_bytes"],0,(region["name"],build))
   for build in ("legacy-beta","pal-prototype-1994-11-29","europe-retail"):
    q=region["builds"][build]
    self.assertEqual(q["aligned_opcode_pairs"],q["aligned_equal_opcode_pairs"],(region["name"],build))
    self.assertEqual(q["aligned_role_disagreements"],0,(region["name"],build))
  self.assertEqual(json.loads(mod.OUTJ.read_text()),r)
  self.assertEqual(mod.OUTM.read_text(),mod.render(r))
  rebuilt=census_mod.build(ROOT)
  self.assertEqual(json.loads((ROOT/"analysis/generated/comparative-structural-census.json").read_text()),rebuilt)
  self.assertEqual((ROOT/"analysis/generated/comparative-structural-census.md").read_text(),census_mod.render(rebuilt))
  print("CAMERA_ISLAND_JSON="+json.dumps(r,sort_keys=True))
if __name__=="__main__": unittest.main()
