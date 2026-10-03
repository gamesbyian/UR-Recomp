import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class RacerReplacementSelectorCppTests(unittest.TestCase):
    def compile_and_run(self, source, exe_name):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            exe = tmp_path / exe_name
            if isinstance(source, pathlib.Path):
                source_path = source
            else:
                source_path = tmp_path / "generated-test.cpp"
                source_path.write_text(source, encoding="utf-8")
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "presentation"),
                    str(ROOT / "native" / "presentation" / "racer_replacement_selector.cpp"),
                    str(source_path),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)

    def test_cpp_contract(self):
        self.compile_and_run(
            ROOT / "tests" / "native" / "racer_replacement_selector_test.cpp",
            "racer-replacement-selector-test",
        )

    def test_native_registration_matches_canonical_json(self):
        registry = json.loads(
            (ROOT / "analysis" / "data" / "racer-hd-replacement-prototype.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertGreaterEqual(len(registry["entries"]), 2)
        representation_ids = [entry["representation_id"] for entry in registry["entries"]]
        self.assertEqual(len(representation_ids), len(set(representation_ids)))

        def hx(value):
            return int(value, 16)

        for entry in registry["entries"]:
            guards = entry["composition_guards"]
            player = {"p1": 1, "p2": 2}[entry["player"]]
            logical_w, logical_h = entry["registration"]["logical_canvas_pixels"]
            occ_x, occ_y = entry["registration"]["occupancy_tile_offset"]
            anchors = entry["registration"]["semantic_anchors"]
            pivot_x2, pivot_y2 = anchors["flip_pivot_x2_y2"]
            contact_x2, contact_y2 = anchors["wheel_contact_x2_y2"]
            source = f"""
#include "racer_replacement_selector.hpp"
#include <cassert>
using namespace ur::presentation;

int main() {{
    RacerCompositionState state{{
        {hx(guards["p1_primary"])},
        {hx(guards["p2_primary"])},
        {hx(guards["p1_companion"])},
        {hx(guards["p2_companion"])},
        {int(guards["p1_selector"])},
        {int(guards["p2_selector"])},
        {hx(guards["p1_companion_gate_word"])},
        {hx(guards["p2_companion_gate_word"])},
    }};
    const auto* r = find_racer_registration_for_state(
        {hx(entry["semantic_frame_id"])}, state
    );
    assert(r != nullptr);
    assert(r->semantic_frame_id == {hx(entry["semantic_frame_id"])});
    assert(r->player == {player});
    assert(r->composition.p1_primary == {hx(guards["p1_primary"])});
    assert(r->composition.p2_primary == {hx(guards["p2_primary"])});
    assert(r->composition.p1_companion == {hx(guards["p1_companion"])});
    assert(r->composition.p2_companion == {hx(guards["p2_companion"])});
    assert(r->composition.p1_selector == {int(guards["p1_selector"])});
    assert(r->composition.p2_selector == {int(guards["p2_selector"])});
    assert(r->composition.p1_companion_gate_word == {hx(guards["p1_companion_gate_word"])});
    assert(r->composition.p2_companion_gate_word == {hx(guards["p2_companion_gate_word"])});
    assert(r->palette_asset_id == {hx(entry["palette_asset_id"])});
    assert(r->logical_width == {logical_w});
    assert(r->logical_height == {logical_h});
    assert(r->occupancy_tile_x == {occ_x});
    assert(r->occupancy_tile_y == {occ_y});
    assert(r->remastered_density_scale == {int(entry["remastered_candidate"]["density_scale"])});
    assert(r->anchor_fixed_point_scale == {int(anchors["fixed_point_scale"])});
    assert(r->has_explicit_pivot);
    assert(r->has_explicit_contact_anchor);
    assert(r->semantic_pivot.x2 == {int(pivot_x2)});
    assert(r->semantic_pivot.y2 == {int(pivot_y2)});
    assert(r->contact_anchor.x2 == {int(contact_x2)});
    assert(r->contact_anchor.y2 == {int(contact_y2)});
    return 0;
}}
"""
            self.compile_and_run(
                source,
                f"racer-replacement-registry-parity-{entry['representation_id']}",
            )



if __name__ == "__main__":
    unittest.main()
