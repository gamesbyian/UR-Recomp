"""Read-only three-project knowledge lookup regression coverage."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from query_upstream_knowledge import address, baldosa_rows, load, mark_rows, search

PIN = "42d444594641d23f5d3c15da7b7c454bb5180e43"


def fixtures():
    native = {"addresses": [
        {"address": "$81:8050", "native": ["src/core/race_progress.cpp:update_checkpoints"]},
        {"address": "$81:8139", "native": ["src/core/race_progress.cpp:cross_start_line"]},
        {"address": "$81:9000", "native": ["src/core/rider_motion.cpp:update_drive"]},
    ]}
    labels = [{"address": "$81:8050", "label": "sub_818050", "class": "observed",
               "comment": "checkpoint", "source_records": ["docs/research/R-1234.md"]}]
    links = {"schema_version": 1, "source": {"commit": PIN}, "entries": [
        {"pal": "81:8050", "correspondence": {"status": "structural-interval-candidate",
                                             "usa": "81:8050", "region": "checkpoint"}},
        {"pal": "81:8139", "correspondence": {"status": "data-interval-only", "usa": "81:8147"}},
    ]}
    return native, labels, links


class UpstreamKnowledgeTest(unittest.TestCase):
    def test_address_and_mirror_without_cross_region_offset(self):
        self.assertEqual(address("$01:8050"), "81:8050")
        self.assertEqual(address("0x818050"), "81:8050")
        self.assertEqual(address("7E:0F09"), "7E:0F09")
        self.assertEqual(address("$0000"), "WRAM:0000")
        self.assertEqual(address("00A1"), "WRAM:00A1")
        self.assertEqual(address("81:8139"), "81:8139")
        with self.assertRaises(ValueError):
            address("81:garbage")

    def test_whole_map_union_retains_native_and_unassessed_addresses(self):
        rows = mark_rows(*fixtures())
        self.assertEqual(len(rows), 3)
        row = rows[0]
        self.assertEqual(row["name"], "sub_818050")
        self.assertEqual(row["source_records"], ["docs/research/R-1234.md"])
        self.assertEqual(row["native"], ["src/core/race_progress.cpp:update_checkpoints"])
        self.assertEqual(rows[-1]["correspondence"]["status"], "not-assessed")

    def test_us_projection_does_not_accept_data_or_uncovered_pal(self):
        mal = mark_rows(*fixtures())
        bald = baldosa_rows([{"address": "818050", "kind": "function", "name": "USA_Check"}])
        results = search(bald + mal, usa="81:8050")
        self.assertEqual({r["source"] for r in results}, {"baldosa", "malmazuke"})
        self.assertEqual(len(search(mal, usa="81:8147")), 0)
        self.assertEqual(len(search(mal, usa="81:9000")), 0)
        self.assertEqual(len(search(mal, exact="81:8050", region="USA")), 0)
        self.assertEqual(len(search(mal, exact="81:8050", region="PAL")), 1)

    def test_query_native_and_source_filters(self):
        rows = baldosa_rows([{"address": "818050", "kind": "function", "name": "Race_Progress"}])
        rows += mark_rows(*fixtures())
        self.assertEqual(len(search(rows, pattern="update_drive")), 1)
        self.assertEqual(len(search(rows, pattern="checkpoint", source="malmazuke")), 1)
        self.assertEqual(len(search(rows, pattern="Race_Progress", source="baldosa")), 1)
        native, labels, links = fixtures()
        links["source"]["commit"] = "stale"
        with self.assertRaises(ValueError):
            mark_rows(native, labels, links)

    def test_duplicate_links_fail_closed(self):
        native, labels, links = fixtures()
        links["entries"].append(links["entries"][0])
        with self.assertRaisesRegex(ValueError, "duplicate PAL"):
            mark_rows(native, labels, links)

    def test_real_pinned_imports_are_queryable(self):
        rows = load()
        self.assertGreater(len([r for r in rows if r["source"] == "baldosa"]), 1000)
        self.assertGreater(len([r for r in rows if r["source"] == "malmazuke"]), 1500)
        self.assertTrue(search(rows, pattern="race_progress.cpp", source="malmazuke"))
        self.assertTrue(search(rows, pattern="Race", source="baldosa"))


if __name__ == "__main__":
    unittest.main()
