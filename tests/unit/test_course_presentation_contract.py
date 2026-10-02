from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import build_course_presentation_contract as contract


class CoursePresentationContractTests(unittest.TestCase):
    def test_dragster_spatial_slab_is_exact_33x1024(self):
        r=contract.build(); s=r["presentation_spatial_contract"]
        self.assertEqual(s["spatial_base_decoded"],0x000F)
        self.assertEqual(s["resource_list_offset"],0x840F)
        self.assertEqual(s["spatial_byte_count"],33*1024)
        self.assertEqual(s["plane_count"],33)
        self.assertEqual(s["runtime_landmarks"]["plane_0_base"],"7F:000F")
        self.assertEqual(s["runtime_landmarks"]["plane_32_base"],"7F:800F")

    def test_dragster_resource_spans_match_confirmed_runtime_plane(self):
        r=contract.build(); x=r["resources"]
        self.assertEqual(x["tail_ids"],[0x01,0x02,0x14,0x24,0x16,0x18])
        self.assertEqual(x["a000_total"],0x200)
        self.assertEqual(x["c000_total"],0x14)
        self.assertEqual(x["checkpoint_finish"]["c000_range"],[6,14])
        self.assertEqual(x["confirmed_c000_snapshot"][6:15],[0x14]*9)

    def test_world_x_query_is_sector_stable(self):
        q=contract.build(1088,1151)["query"]
        self.assertEqual(q["sector_indices"],[17])
        self.assertEqual(len(q["records"][0]["attributes"]),33)

    def test_historical_finish_probe_lands_inside_1024_sector_domain(self):
        r=contract.build()
        f=next(a for a in r["presentation_spatial_contract"]["anchors"] if a["name"]=="historical_finish_probe")
        self.assertEqual(f["world_x"],25278)
        self.assertEqual(f["sector_index"],394)
        self.assertTrue(0<=f["sector_index"]<1024)


if __name__=="__main__":
    unittest.main()
