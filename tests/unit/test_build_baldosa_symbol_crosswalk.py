"""Test the external-symbol crosswalk without mutating the canonical symbol database."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from build_baldosa_symbol_crosswalk import crosswalk, local_addresses


class CrosswalkTest(unittest.TestCase):
    def test_lorom_cpu_mirrors_canonicalize(self):
        self.assertEqual(local_addresses("`01:8B95` (USA)"), {"818B95"})
        self.assertEqual(local_addresses("`00:8584` / `80:8584` mirror"), {"808584"})
        self.assertEqual(local_addresses("`7E:0F09`"), {"7E0F09"})
        self.assertEqual(local_addresses("TBD"), set())

    def test_overlap_does_not_promote_external_labels(self):
        local = [
            {"kind": "function", "address": "01:8B95", "name": "CourseSampler"},
            {"kind": "ram", "address": "7E:0F09", "name": "Contact"},
            {"kind": "function", "address": "not-an-address", "name": "Unknown"},
        ]
        ext = [
            {"kind": "function", "address": "818B95", "name": "Uni_ProbeCollision"},
            {"kind": "ram", "address": "7E0F09", "name": "Contact"},
            {"kind": "function", "address": "83E7A5", "name": "Race_UpdateFinish"},
        ]
        report = crosswalk(local, ext)
        self.assertEqual(report["skipped_local_unparseable_rows"], 1)
        self.assertEqual(report["counts"], {
            "same_name": 1, "different_names": 1,
            "external_only": 1, "local_only": 0,
        })
        diff = [x for x in report["rows"] if x["status"] == "different_names"][0]
        self.assertEqual(diff["address"], "81:8B95")
        self.assertEqual(diff["local_names"], ["CourseSampler"])


if __name__ == "__main__":
    unittest.main()
