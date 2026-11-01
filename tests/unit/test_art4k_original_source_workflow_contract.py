"""Fast stdlib-only contracts for the bounded, opt-in ART-4K original corpus job."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
JOB = ROOT / ".github/workflows/art4k-original-source-family-corpus.yml"


class SourceWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = JOB.read_text(encoding="utf-8")

    def test_targeted_dispatch_and_no_scheduled_background_job(self):
        raw = self.text
        self.assertIn("workflow_dispatch:", raw)
        self.assertIn("pull_request:", raw)
        self.assertIn('".github/workflows/art4k-original-source-family-corpus.yml"', raw)
        self.assertIn("cancel-in-progress: true", raw)
        self.assertNotIn("\n  schedule:", raw)
        self.assertNotIn("\n  push:", raw)

    def test_real_canonical_rom_checked_before_actual_existing_exporter(self):
        raw = self.text
        verify = raw.index("python3 tools/verify_rom.py")
        sha = raw.index('hashlib.sha256(raw).hexdigest()')
        export = raw.index("python3 tools/art/export_registered_original_racer_corpus.py")
        freeze = raw.index("python3 tools/art/freeze_racer_source_family_splits.py")
        upload = raw.index("uses: actions/upload-artifact@v4")
        self.assertLess(verify, sha)
        self.assertLess(sha, export)
        self.assertLess(export, freeze)
        self.assertLess(freeze, upload)
        self.assertIn("859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478", raw)
        self.assertIn("source-corpus.json", raw)
        self.assertIn("diagnostic-source-family-groups.json", raw)

    def test_artifact_contains_only_registered_output_tree_not_rom(self):
        raw = self.text
        self.assertIn("path: ${{ runner.temp }}/art4k-original-source-corpus/", raw)
        self.assertNotIn("path: reference/roms/", raw)
        self.assertNotIn("path: ${{ github.workspace }}", raw)
        self.assertIn("retention-days: 7", raw)
        self.assertIn("if-no-files-found: error", raw)
        self.assertIn("persist-credentials: false", raw)
        self.assertIn("contents: read", raw)
        self.assertNotIn("secrets.", raw)

    def test_no_false_original_camera_or_holdout_approval(self):
        raw = self.text
        self.assertIn('"diagnostic"]["window_count"] == expected_windows', raw)
        self.assertIn('"fit"]["window_count"] == 0', raw)
        self.assertIn('"withheld_candidate"]["window_count"] == 0', raw)
        self.assertIn('"owner_likeness_approved"] is False', raw)
        self.assertIn('"shipping_art_approved"] is False', raw)
        self.assertIn('"source_3d_geometry_recovered"] is False', raw)
        self.assertIn('"no_original_binary_silhouette_across_roles"] is True', raw)


if __name__ == "__main__":
    unittest.main()
