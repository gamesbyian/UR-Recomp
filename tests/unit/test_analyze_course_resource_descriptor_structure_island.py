import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import analyze_course_resource_descriptor_structure_island as mod

class CourseResourceDescriptorIslandTest(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(mod.REGIONS[0][1], "82:B293")
        self.assertEqual(mod.REGIONS[-1][2], "82:B32E")
        total = sum(mod.cpu_to_offset(e) - mod.cpu_to_offset(s) + 1 for _, s, e in mod.REGIONS)
        self.assertEqual(total, mod.cpu_to_offset("82:B32E") - mod.cpu_to_offset("82:B293") + 1)

    def test_rom_probe(self):
        if not all(p.exists() for p in mod.ROMS.values()):
            self.skipTest("ROM corpus absent")
        result = mod.build()
        self.assertEqual(result["usa_start"], "82:B293")
        self.assertEqual(result["usa_end"], "82:B32E")
        self.assertEqual(result["next_region"], "82:B32F")
        self.assertEqual(result["relationship"]["descriptor_record_stride"], 5)
        self.assertEqual(len(result["regions"]), 4)
        for region in result["regions"]:
            self.assertEqual(region["builds"]["legacy-beta"]["similarity"], 1.0, region["name"])
            self.assertEqual(region["builds"]["usa-retail"]["unreached_or_data_bytes"], 0, region["name"])
            for build in ("legacy-beta", "pal-prototype-1994-11-29", "europe-retail"):
                item = region["builds"][build]
                self.assertEqual(item["aligned_role_disagreements"], 0, (region["name"], build))
                self.assertEqual(item["aligned_opcode_pairs"], item["aligned_equal_opcode_pairs"], (region["name"], build))

if __name__ == "__main__":
    unittest.main()
