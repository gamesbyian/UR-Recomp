from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import analyze_course_materialization_structure_island as mod

def test_region_partition_is_bounded_and_ordered():
    expected=[
        ("setup","82:E165","82:E1CF"),
        ("resource_record_header","82:E1D1","82:E213"),
        ("dma_row_loop","82:E216","82:E2FF"),
        ("resource_materialize_A000_C000","82:E302","82:E385"),
        ("exit","82:E388","82:E395"),
    ]
    assert [(n,s,e) for n,s,e,_ in mod.REGIONS] == expected
    assert all(kind=="code" for *_,kind in mod.REGIONS)

def test_render_describes_materialization_boundaries():
    fake={"regions":[{"name":"setup","size":1,"builds":{
        b:{"start":"82:E165","end":"82:E165","shift":0,"similarity":1.0,"opcode_bytes":1,"unreached_or_data_bytes":0}
        for b in ("usa-retail","pal-prototype-1994-11-29","europe-retail","legacy-beta")
    }}]}
    text=mod.render(fake)
    assert "A000/C000" in text
    assert "resource cursor" in text


def test_rom_backed_course_island_when_roms_present():
    if not all(path.exists() for path in mod.ROMS.values()):
        return
    result=mod.build()
    assert len(result["regions"]) == 5
    for region in result["regions"]:
        assert region["builds"]["usa-retail"]["opcode_bytes"] > 0
        assert region["builds"]["legacy-beta"]["similarity"] == 1.0
    # Existing trusted homolog corpus already establishes the common Europe shift
    # through the first three partitions; preserve that as a regression oracle.
    for region in result["regions"][:3]:
        assert region["builds"]["europe-retail"]["shift"] == -58
    print("COURSE_ISLAND_TEST_JSON="+__import__("json").dumps(result,sort_keys=True))
