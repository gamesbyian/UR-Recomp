from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import build_course_presentation_contract as contract


class CoursePresentationContractTests(unittest.TestCase):
    def test_dragster_world_and_two_level_spatial_contract(self):
        r=contract.build()
        self.assertEqual(r["course"]["header_dims"],[256,4])
        self.assertEqual(r["world_contract"]["coarse_grid"],[1024,16])
        self.assertEqual(r["world_contract"]["world_extent"],[65536,1024])
        self.assertEqual(r["world_contract"]["camera_wrap_or_clamp_masks"]["x_0D49"],0xFFFF)
        self.assertEqual(r["world_contract"]["camera_wrap_or_clamp_masks"]["y_0D47"],0x03FF)
        coarse=r["spatial_tables"]["coarse_sector_index"]
        fine=r["spatial_tables"]["fine_record_table"]
        self.assertEqual(coarse["decoded_base"],0x000F)
        self.assertEqual(coarse["entry_count"],16384)
        self.assertEqual(coarse["byte_length"],0x8000)
        self.assertEqual(fine["decoded_base"],0x800F)
        self.assertEqual(fine["record_bytes"],32)
        self.assertEqual(fine["record_count"],32)

    def test_dragster_resource_spans_match_confirmed_runtime_plane(self):
        r=contract.build(); x=r["resources"]
        self.assertEqual(x["tail_ids"],[0x01,0x02,0x14,0x24,0x16,0x18])
        self.assertEqual(x["a000_total"],0x200)
        self.assertEqual(x["c000_total"],0x14)
        self.assertEqual(x["checkpoint_finish"]["c000_range"],[6,14])
        self.assertEqual(x["confirmed_c000_snapshot"][6:15],[0x14]*9)

    def test_spawn_region_query_maps_to_materialized_owners(self):
        q=contract.build((1088,800,1151,863))["query"]
        self.assertEqual(q["fine_cell_count"],16)
        self.assertTrue(q["fine_record_ids"])
        for cell in q["cells"]:
            if cell["kind"]=="materialized_surface":
                self.assertIsNotNone(cell["resource_id"])
                self.assertIsNotNone(cell["c000_slot"])
                self.assertIsNotNone(cell["a000_range"])

    def test_historical_finish_probe_is_inside_runtime_world_extent(self):
        r=contract.build()
        self.assertEqual(r["course"]["historical_finish_x_probe"],25278)
        self.assertLess(r["course"]["historical_finish_x_probe"],r["world_contract"]["world_extent"][0])

    def test_checkpoint_resource_has_spatial_placements(self):
        cp=contract.build()["resources"]["checkpoint_finish"]
        self.assertEqual(cp["behavior_code"],0x14)
        self.assertTrue(cp["fine_record_ids"])
        self.assertGreater(cp["coarse_sector_placement_count"],0)


if __name__=="__main__":
    unittest.main()
