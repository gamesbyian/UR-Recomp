from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import build_course_presentation_contract as contract

def test_dragster_spatial_slab_is_exact_33x1024():
    r=contract.build(); s=r["presentation_spatial_contract"]
    assert s["spatial_base_decoded"]==0x000F
    assert s["resource_list_offset"]==0x840F
    assert s["spatial_byte_count"]==33*1024
    assert s["plane_count"]==33
    assert s["runtime_landmarks"]["plane_0_base"]=="7F:000F"
    assert s["runtime_landmarks"]["plane_32_base"]=="7F:800F"

def test_dragster_resource_spans_match_confirmed_runtime_plane():
    r=contract.build(); x=r["resources"]
    assert x["tail_ids"]==[0x01,0x02,0x14,0x24,0x16,0x18]
    assert x["a000_total"]==0x200
    assert x["c000_total"]==0x14
    assert x["checkpoint_finish"]["c000_range"]==[6,14]
    assert x["confirmed_c000_snapshot"][6:15]==[0x14]*9

def test_world_x_query_is_sector_stable():
    q=contract.build(1088,1151)["query"]
    assert q["sector_indices"]==[17]
    assert len(q["records"][0]["attributes"])==33

def test_historical_finish_probe_lands_inside_1024_sector_domain():
    r=contract.build()
    f=next(a for a in r["presentation_spatial_contract"]["anchors"] if a["name"]=="historical_finish_probe")
    assert f["world_x"]==25278
    assert f["sector_index"]==394
    assert 0<=f["sector_index"]<1024
