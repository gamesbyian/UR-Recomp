"""Pin file-by-file upstream inventory and deliberate generated-file exclusions."""
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import audit_baldosa_source_census as mod


class BaldosaCensusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.census = json.loads(mod.CENSUS.read_text(encoding="utf-8"))
        cls.manifest = json.loads(mod.MANIFEST.read_text(encoding="utf-8"))

    def test_complete_pinned_intake(self):
        self.assertEqual(mod.validate(self.census, self.manifest), [])

    def test_missing_authored_file_is_rejected(self):
        data = copy.deepcopy(self.census)
        row = next(x for x in data["entries"] if x["path"] == "web/netplay.js")
        row["disposition"] = "metadata-only-generated"
        errors = mod.validate(data, self.manifest)
        self.assertTrue(any("unclassified omission" in e or "disagreement" in e for e in errors))

    def test_bad_upstream_provenance_is_rejected(self):
        bad = copy.deepcopy(self.manifest)
        row = next(x for x in bad["entries"] if x["path"].endswith("/web/settings.js"))
        row["upstream_git_blob_sha1"] = "0" * 40
        self.assertTrue(any("provenance mismatch" in e for e in mod.validate(self.census, bad)))

    def test_submodule_change_is_detected(self):
        data = copy.deepcopy(self.census)
        next(x for x in data["entries"] if x["path"] == "snesrecomp")["sha"] = "0" * 40
        self.assertTrue(any("submodule" in e for e in mod.validate(data, self.manifest)))


if __name__ == "__main__":
    unittest.main()
