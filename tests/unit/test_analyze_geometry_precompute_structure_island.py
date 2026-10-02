import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import analyze_geometry_precompute_structure_island as mod
import build_comparative_structural_census as census_mod


class GeometryPrecomputeIslandTest(unittest.TestCase):
    def test_rom_probe(self):
        if not all(path.exists() for path in mod.ROMS.values()):
            self.skipTest("ROMs absent")

        result = mod.build()
        self.assertEqual(result["long_entry"], "81:99D6")
        self.assertEqual(result["body_entry"], "81:9A5A")
        self.assertEqual(result["next_entry"], "81:9E2A")
        self.assertEqual(sum(region["size"] for region in result["regions"]), 1108)

        self.assertTrue(all(result["table_identity_by_build"].values()))

        for region in result["regions"]:
            beta = region["builds"]["legacy-beta"]
            self.assertEqual(beta["similarity"], 1.0, region["name"])
            if region["kind"] == "code":
                self.assertEqual(
                    region["builds"]["usa-retail"]["unreached_or_data_bytes"],
                    0,
                    region["name"],
                )
                for build in (
                    "legacy-beta",
                    "pal-prototype-1994-11-29",
                    "europe-retail",
                ):
                    item = region["builds"][build]
                    self.assertEqual(
                        item["aligned_opcode_pairs"],
                        item["aligned_equal_opcode_pairs"],
                        (region["name"], build),
                    )
                    self.assertEqual(
                        item["aligned_role_disagreements"],
                        0,
                        (region["name"], build),
                    )

        self.assertEqual(json.loads(mod.OUTJ.read_text()), result)
        self.assertEqual(mod.OUTM.read_text(), mod.render(result))
        rebuilt = census_mod.build(ROOT)
        self.assertEqual(json.loads((ROOT / "analysis/generated/comparative-structural-census.json").read_text()), rebuilt)
        self.assertEqual((ROOT / "analysis/generated/comparative-structural-census.md").read_text(), census_mod.render(rebuilt))

        print("GEOMETRY_PRECOMPUTE_JSON=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
