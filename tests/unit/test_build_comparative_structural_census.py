import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_comparative_structural_census as census


def test_builds_seed_census_from_structural_islands(tmp_path):
    generated = tmp_path / "analysis" / "generated"
    generated.mkdir(parents=True)
    racer = {
        "regions": [{
            "name": "routine",
            "kind": "code",
            "usa_start": "82:A000",
            "usa_end": "82:A003",
            "size": 4,
            "builds": {
                "usa-retail": {"start": "82:A000", "end": "82:A003", "shift": 0, "similarity": 1.0, "opcode_bytes": 2, "operand_bytes": 2, "unreached_or_data_bytes": 0},
                "europe-retail": {"start": "82:A004", "end": "82:A007", "shift": 4, "similarity": 0.75},
            },
        }]
    }
    obj = {
        "regions": [{
            "name": "table",
            "kind": "data",
            "usa_start": "81:9000",
            "usa_end": "81:9003",
            "size": 4,
            "builds": {
                "usa-retail": {"start": "81:9000", "end": "81:9003", "shift": 0, "similarity": 1.0, "opcode_bytes": 0, "operand_bytes": 0, "unreached_or_data_bytes": 4},
            },
        }]
    }
    (generated / "racer-update-structure-island.json").write_text(json.dumps(racer))
    (generated / "object-collision-structure-island.json").write_text(json.dumps(obj))
    result = census.build(tmp_path)
    assert result["totals"]["regions"] == 2
    assert result["totals"]["code_regions"] == 1
    assert result["totals"]["data_regions"] == 1
    assert result["totals"]["bounded_bytes"] == 8
    assert result["totals"]["analyzer_opcode_bytes"] == 2
    assert result["totals"]["banks"] == ["81", "82"]
    assert result["regions"][0]["usa_start"] == "81:9000"
    assert result["regions"][1]["homologs"]["europe-retail"]["shift"] == 4


def test_optional_course_island_expands_census(tmp_path):
    generated = tmp_path / "analysis" / "generated"
    generated.mkdir(parents=True)
    empty = {"regions": []}
    (generated / "racer-update-structure-island.json").write_text(json.dumps(empty))
    (generated / "object-collision-structure-island.json").write_text(json.dumps(empty))
    course = {
        "regions": [{
            "name": "course_exit",
            "kind": "code",
            "usa_start": "82:E388",
            "usa_end": "82:E395",
            "size": 14,
            "builds": {
                "usa-retail": {"start": "82:E388", "end": "82:E395", "shift": 0, "similarity": 1.0, "opcode_bytes": 6, "operand_bytes": 8, "unreached_or_data_bytes": 0},
                "europe-retail": {"start": "82:E34E", "end": "82:E35B", "shift": -58, "similarity": 0.9},
            },
        }]
    }
    (generated / "course-materialization-structure-island.json").write_text(json.dumps(course))
    result = census.build(tmp_path)
    assert result["totals"]["regions"] == 1
    assert result["totals"]["bounded_bytes"] == 14
    assert result["regions"][0]["source"] == "course-materialization"
    assert {source["id"] for source in result["sources"]} == {"racer-update", "object-collision", "course-materialization"}
