import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import analyze_course_materialization_structure_island as mod


class CourseMaterializationStructureTests(unittest.TestCase):
    def test_region_partition_is_bounded_and_ordered(self):
        expected=[
            ("setup","82:E165","82:E1CF"),
            ("resource_record_header","82:E1D1","82:E213"),
            ("dma_row_loop","82:E216","82:E2FF"),
            ("resource_materialize_A000_C000","82:E302","82:E385"),
            ("exit","82:E388","82:E395"),
        ]
        self.assertEqual([(n,s,e) for n,s,e,_ in mod.REGIONS], expected)
        self.assertTrue(all(kind=="code" for *_,kind in mod.REGIONS))

    def test_render_describes_materialization_boundaries(self):
        fake={"regions":[{"name":"setup","size":1,"builds":{
            b:{"start":"82:E165","end":"82:E165","shift":0,"similarity":1.0,"opcode_bytes":1,"unreached_or_data_bytes":0}
            for b in ("usa-retail","pal-prototype-1994-11-29","europe-retail","legacy-beta")
        }}]}
        text=mod.render(fake)
        self.assertIn("A000/C000", text)
        self.assertIn("resource cursor", text)

    def test_rom_backed_course_island_when_roms_present(self):
        if not all(path.exists() for path in mod.ROMS.values()):
            self.skipTest("preserved ROM corpus not present")
        result=mod.build()
        self.assertEqual(len(result["regions"]), 5)
        for region in result["regions"]:
            self.assertGreater(region["builds"]["usa-retail"]["opcode_bytes"], 0)
            self.assertEqual(region["builds"]["legacy-beta"]["similarity"], 1.0)
        for region in result["regions"][:3]:
            self.assertEqual(region["builds"]["europe-retail"]["shift"], -58)
        print("COURSE_ISLAND_TEST_JSON="+json.dumps(result,sort_keys=True))


if __name__=="__main__":
    unittest.main()
