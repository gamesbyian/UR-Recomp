import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import analyze_course_surface_sampler_structure_island as mod

class CourseSurfaceSamplerTests(unittest.TestCase):
    def test_bounds_and_size(self):
        self.assertEqual(mod.USA_START,"81:8B95")
        self.assertEqual(mod.USA_END,"81:8D13")
        self.assertEqual(mod.cpu_to_offset(mod.USA_END)-mod.cpu_to_offset(mod.USA_START)+1,383)

    def test_rom_backed_probe_when_roms_present(self):
        if not all(path.exists() for path in mod.ROMS.values()):
            self.skipTest("preserved ROM corpus not present")
        result=mod.build()
        self.assertEqual(result["usa_size"],383)
        self.assertGreater(result["builds"]["usa-retail"]["opcode_bytes"],0)
        self.assertEqual(result["builds"]["usa-retail"]["unreached_or_data_bytes"],0)
        self.assertEqual(result["builds"]["legacy-beta"]["similarity"],1.0)
        self.assertEqual(result["builds"]["pal-prototype-1994-11-29"]["shift"],-32)
        self.assertEqual(result["builds"]["europe-retail"]["shift"],-32)
        self.assertEqual(len(result["regions"]),1)
        self.assertEqual(result["regions"][0]["name"],"Course_SampleRuntimeSurface")
        print("COURSE_SURFACE_SAMPLER_JSON="+json.dumps(result,sort_keys=True))

if __name__=="__main__":
    unittest.main()
