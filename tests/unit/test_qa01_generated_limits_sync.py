"""Guard source-backed QA01 limitations against stale checked-in generated prose."""

import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class QA01GeneratedLimitSyncTests(unittest.TestCase):
    def test_census_limit_lines_match_source_generator(self):
        source = (ROOT / "tools/audit_original_course_event_coverage.py").read_text()
        tree = ast.parse(source)
        candidates = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == "limits":
                    candidates.append(ast.literal_eval(value))
        self.assertEqual(len(candidates), 1, "expected exactly one generator limit list")
        generated = json.loads((ROOT / "analysis/generated/course-event-qa-census.json")
                               .read_text(encoding="utf-8"))
        self.assertEqual(generated["limits"], candidates[0])


if __name__ == "__main__":
    unittest.main()
