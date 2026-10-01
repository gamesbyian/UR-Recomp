#!/usr/bin/env python3
import unittest

from tools.build_wram_motion_atlas import build_lineage_motion, signed_delta, summarize


class WramMotionAtlasTests(unittest.TestCase):
    def test_signed_delta_wraps_to_signed_16bit(self):
        self.assertEqual(signed_delta(0x1000, 0x1004), 4)
        self.assertEqual(signed_delta(0x1004, 0x1000), -4)

    def test_summarize_clusters_shared_motion_and_flags_conflicts(self):
        rows = [
            {
                "build": "pal",
                "anchor": "A",
                "anchor_candidate_cpu": "82:9000",
                "anchor_byte_similarity": 0.95,
                "usa_word": "1000",
                "candidate_word": "1004",
                "delta": 4,
                "evidence_count": 2,
                "source_occurrences": 2,
            },
            {
                "build": "pal",
                "anchor": "B",
                "anchor_candidate_cpu": "82:A000",
                "anchor_byte_similarity": 0.96,
                "usa_word": "1000",
                "candidate_word": "1004",
                "delta": 4,
                "evidence_count": 1,
                "source_occurrences": 1,
            },
            {
                "build": "pal",
                "anchor": "B",
                "anchor_candidate_cpu": "82:A000",
                "anchor_byte_similarity": 0.96,
                "usa_word": "1100",
                "candidate_word": "1104",
                "delta": 4,
                "evidence_count": 1,
                "source_occurrences": 1,
            },
            {
                "build": "europe",
                "anchor": "A",
                "anchor_candidate_cpu": "82:9000",
                "anchor_byte_similarity": 0.90,
                "usa_word": "1200",
                "candidate_word": "120A",
                "delta": 10,
                "evidence_count": 1,
                "source_occurrences": 1,
            },
            {
                "build": "europe",
                "anchor": "B",
                "anchor_candidate_cpu": "82:A000",
                "anchor_byte_similarity": 0.91,
                "usa_word": "1200",
                "candidate_word": "1206",
                "delta": 6,
                "evidence_count": 1,
                "source_occurrences": 1,
            },
        ]
        atlas = summarize(rows)

        pal_plus4 = next(c for c in atlas["clusters"] if c["build"] == "pal" and c["delta"] == 4)
        self.assertEqual(pal_plus4["anchor_count"], 2)
        self.assertEqual(pal_plus4["field_count"], 2)
        self.assertEqual(pal_plus4["evidence_count"], 4)

        pal_field = next(
            f for f in atlas["field_consistency"]
            if f["build"] == "pal" and f["usa_word"] == "1000"
        )
        self.assertTrue(pal_field["consistent"])
        self.assertEqual(pal_field["candidate_words"], ["1004"])

        self.assertEqual(
            atlas["contradictions"],
            [{
                "build": "europe",
                "usa_word": "1200",
                "candidate_words": ["1206", "120A"],
                "deltas": [6, 10],
                "anchors": ["A", "B"],
                "consistent": False,
            }],
        )

    def test_groups_secondary_motion_between_prototype_and_europe(self):
        rows = [
            {
                "build": "pal-prototype-1994-11-29",
                "usa_word": "0F9F",
                "candidate_words": ["0FA3"],
                "deltas": [4],
                "anchors": ["A", "B"],
                "consistent": True,
            },
            {
                "build": "europe-retail",
                "usa_word": "0F9F",
                "candidate_words": ["0FA9"],
                "deltas": [10],
                "anchors": ["A", "B"],
                "consistent": True,
            },
            {
                "build": "pal-prototype-1994-11-29",
                "usa_word": "0411",
                "candidate_words": ["0411"],
                "deltas": [0],
                "anchors": ["C"],
                "consistent": True,
            },
            {
                "build": "europe-retail",
                "usa_word": "0411",
                "candidate_words": ["0415"],
                "deltas": [4],
                "anchors": ["C"],
                "consistent": True,
            },
        ]
        out = build_lineage_motion(rows)
        by_delta = {x["prototype_to_europe_delta"]: x for x in out["clusters"]}
        self.assertEqual(by_delta[6]["usa_words"], ["0F9F"])
        self.assertEqual(by_delta[4]["usa_words"], ["0411"])


if __name__ == "__main__":
    unittest.main()
