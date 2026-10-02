import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class RacerGuestSnapshotCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "racer-guest-snapshot-test"
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
                    str(ROOT / "native" / "presentation" / "racer_guest_snapshot.cpp"),
                    str(ROOT / "tests" / "native" / "racer_guest_snapshot_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)

    def test_native_addresses_match_canonical_presentation_contract(self):
        assets = json.loads(
            (ROOT / "analysis" / "data" / "presentation-assets.json").read_text(
                encoding="utf-8"
            )
        )
        family = next(
            x for x in assets["families"]
            if x["id"] == "ordinary-race-racer-presentation"
        )
        contract = family["composition_contract"]

        def addr(value):
            return int(value.lstrip("$"), 16)

        expected = {
            "p1_primary": addr(contract["records"]["p1_primary"]),
            "p2_primary": addr(contract["records"]["p2_primary"]),
            "p1_companion": addr(contract["records"]["p1_companion"]),
            "p2_companion": addr(contract["records"]["p2_companion"]),
            "p1_selector": addr(contract["selectors"]["p1"]),
            "p2_selector": addr(contract["selectors"]["p2"]),
            "p1_companion_gate": addr(contract["companion_gates"]["p1"].split()[0]),
            "p2_companion_gate": addr(contract["companion_gates"]["p2"].split()[0]),
        }

        source = """
#include "racer_guest_snapshot.hpp"
#include <cassert>
using namespace ur::presentation;
int main() {
"""
        for name, value in expected.items():
            source += f"    static_assert(RacerGuestAddresses::{name} == 0x{value:04X});\n"
        source += "    static_assert(RacerGuestAddresses::wram_size == 0x20000);\n    return 0;\n}\n"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            source_path = tmp_path / "address-parity.cpp"
            exe = tmp_path / "address-parity"
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
                    str(source_path),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
