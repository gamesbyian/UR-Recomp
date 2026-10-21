#!/usr/bin/env python3
import json
from pathlib import Path
import tempfile
import unittest

from tests.unit.test_qa_modern_visual_diagnostics import (
    BAR, FG, logical_canvas, p7, put, render)
from tools import qa_modern_visual_report as r


def write(path, frame):
    path.write_bytes(p7(frame.width, frame.height,
                        [frame.rgb(x, y) for y in range(frame.height)
                         for x in range(frame.width)]))


class ReportTest(unittest.TestCase):
    def setUp(self):
        grid, w, h = logical_canvas(256, 224)
        put(grid, w, 30, 30, 40, 8, FG)
        put(grid, w, 20, 60, 3, 16, BAR)
        self.frame = render(grid, w, h, 1024, 768)

    def manifest(self, root, **over):
        write(root / "a.p7", self.frame)
        case = {"id": "root-43", "p7": "a.p7", "expect_sha256": self.frame.sha256,
                "checks": [
                    {"type": "clip", "logical": [256, 224], "colours": ["#c8c8c8"]},
                    {"type": "focus", "marker": "#a0d0f8", "scale": 3}]}
        case.update(over)
        return {"cases": [case]}

    def test_pass_fail_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rep = r.run_manifest(self.manifest(root), root)
            self.assertEqual(rep["status"], "pass", rep)
            self.assertIn("root-43", r.markdown(rep))
            bad = self.manifest(root)
            bad["cases"][0]["checks"][1]["marker"] = "#010203"
            self.assertEqual(r.run_manifest(bad, root)["status"], "fail")
            bad = self.manifest(root, expect_sha256="0" * 64)
            self.assertEqual(r.run_manifest(bad, root)["status"], "incomplete")
            bad = self.manifest(root, p7="missing.p7")
            self.assertEqual(r.run_manifest(bad, root)["status"], "incomplete")
            self.assertEqual(r.run_manifest({"cases": []}, root)["status"], "incomplete")
            dup = self.manifest(root)
            dup["cases"].append(dup["cases"][0])
            self.assertEqual(r.run_manifest(dup, root)["status"], "incomplete")
            self.assertEqual(rep["release_gate_credit"], 0)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "m.json").write_text(json.dumps(self.manifest(root)))
            summary = root / "s.md"
            self.assertEqual(r.main([str(root / "m.json"), "--json", str(root / "o.json"),
                                     "--summary", str(summary)]), 0)
            self.assertIn("pass", summary.read_text())
            (root / "m.json").write_text("{")
            self.assertEqual(r.main([str(root / "m.json")]), 1)


if __name__ == "__main__":
    unittest.main()
