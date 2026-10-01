import unittest

from tools.probe_wram_insertion_brackets import trusted_europe_projection_targets


class WramInsertionBracketProbeTests(unittest.TestCase):
    def test_projection_targets_explain_numeric_only_europe_addresses(self):
        corpus = {
            "anchors": [
                {
                    "name": "camera",
                    "matches": {
                        "europe-retail": [
                            {
                                "byte_similarity": 0.9,
                                "semantic_word_projection": {
                                    "0539": {
                                        "dominant_candidate": "053D",
                                        "dominant_count": 2,
                                        "source_occurrences": 2,
                                    }
                                },
                            }
                        ]
                    },
                },
                {
                    "name": "weak",
                    "matches": {
                        "europe-retail": [
                            {
                                "byte_similarity": 0.2,
                                "semantic_word_projection": {
                                    "1000": {
                                        "dominant_candidate": "1004",
                                        "dominant_count": 1,
                                        "source_occurrences": 1,
                                    }
                                },
                            }
                        ]
                    },
                },
            ]
        }
        targets = trusted_europe_projection_targets(corpus)
        self.assertIn("053D", targets)
        self.assertNotIn("1004", targets)


if __name__ == "__main__":
    unittest.main()
