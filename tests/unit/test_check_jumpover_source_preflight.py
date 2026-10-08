"""Pin recovered Jumpover sources before they can be used as fidelity evidence."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from check_jumpover_source_preflight import (  # noqa: E402
    EvidenceError, blob_sha1, input_runs, unique_routes, verify_preflight,
)

EVIDENCE = ROOT / "analysis/generated/jumpover-fallthrough-source-preflight.json"


class JumpoverSourcePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def check_tamper(self, mutate, message):
        doc = copy.deepcopy(self.evidence)
        mutate(doc)
        with self.assertRaisesRegex(EvidenceError, message):
            verify_preflight(ROOT, doc)

    def test_pinned_movies_and_scripts_still_match(self):
        result = verify_preflight(ROOT, self.evidence)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["native_admitted"])
        self.assertEqual([r["route"] for r in result["routes"]], ["left", "right"])
        self.assertEqual([r["controller_samples"] for r in result["routes"]], [53, 73])

    def test_git_blob_and_run_length_encoding(self):
        self.assertEqual(blob_sha1(b"hello"), "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0")
        self.assertEqual(input_runs([0x0200, 0x0200, 0x82A0, 0x0000]), [
            {"start": 0, "duration": 2, "mask": "0200"},
            {"start": 2, "duration": 1, "mask": "82a0"},
            {"start": 3, "duration": 1, "mask": "0000"},
        ])

    def test_changed_movie_blob_rejected(self):
        self.check_tamper(lambda d: d["movies"][0].update(git_blob_sha1="0" * 40), "left SMV blob")

    def test_changed_controller_runs_rejected(self):
        self.check_tamper(lambda d: d["movies"][0]["raw_input_runs"][0].update(duration=2), "left raw input runs")

    def test_changed_anchor_rejected(self):
        self.check_tamper(lambda d: d["movies"][0]["embedded_anchor"].update(wram_sha256="0" * 64), "left WRAM SHA256")

    def test_changed_lua_blob_rejected(self):
        self.check_tamper(lambda d: d["historical_scripts"][0].update(git_blob_sha1="0" * 40), "left Lua blob")

    def test_changed_sweep_rejected(self):
        self.check_tamper(lambda d: d["historical_scripts"][1]["x_sweep"].update(stop=2700), "right X sweep")

    def test_duplicate_route_rejected(self):
        with self.assertRaisesRegex(EvidenceError, "one left and one right"):
            unique_routes([{"route": "left"}, {"route": "left"}], "movies")

    def test_missing_source_rejected(self):
        self.check_tamper(lambda d: d["movies"][0].update(path="reference/not-here.smv"), "cannot read")

    def test_path_traversal_rejected(self):
        self.check_tamper(lambda d: d["movies"][0].update(path="../../etc/passwd"), "escapes repository")

    def test_schema_and_kind_fail_closed(self):
        self.check_tamper(lambda d: d.update(schema_version=2), "schema_version")
        self.check_tamper(lambda d: d.update(kind="native-admitted"), "kind")


if __name__ == "__main__":
    unittest.main()
