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
        self.assertEqual(len(registry["entries"]), 1)
        entry = registry["entries"][0]
        guards = entry["composition_guards"]

        def hx(value):
            return int(value, 16)

        player = {"p1": 1, "p2": 2}[entry["player"]]
        logical_w, logical_h = entry["registration"]["logical_canvas_pixels"]
        occ_x, occ_y = entry["registration"]["occupancy_tile_offset"]
        source = f"""
#include "racer_replacement_selector.hpp"
#include <cassert>
using namespace ur::presentation;

int main() {{
    const auto* r = find_racer_registration({hx(entry["semantic_frame_id"])});
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
    assert(!r->has_explicit_pivot);
    assert(!r->has_explicit_contact_anchor);
    return 0;
}}
"""
        self.compile_and_run(source, "racer-replacement-registry-parity-test")


if __name__ == "__main__":
    unittest.main()
