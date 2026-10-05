import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class QuickPracticeCatalogTests(unittest.TestCase):
    def test_shipping_catalog_matches_canonical_course_corpus(self):
        corpus = json.loads((ROOT / "analysis/data/course-corpus.json").read_text())
        header = (ROOT / "native/product/quick_practice_catalog.hpp").read_text()

        rows = re.findall(
            r'\{(\d+), "([^"]+)", "([^"]+)", (\d+), (\d+), QuickPracticeCourseKind::(\w+)\},',
            header,
        )
        self.assertEqual(len(rows), 45)

        kind_map = {
            "race-a": "Race",
            "race-b": "Race",
            "circuit-a": "Circuit",
            "circuit-b": "Circuit",
            "stunt": "Stunt",
        }
        expected = []
        for course in corpus["courses"]:
            expected.append(
                (
                    str(course["stream_index"] - 1),
                    course["name"],
                    course["tour"],
                    str(course["tour_index"]),
                    str(course["tour_slot"] - 1),
                    kind_map[course["track_kind"]],
                )
            )
        self.assertEqual(rows, expected)


if __name__ == "__main__":
    unittest.main()
