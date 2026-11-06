"""Cost-bounded opt-in original manual figure artifact, no recurring CI."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]


class OriginalManualOnDemandWorkflowContractTests(unittest.TestCase):
    def test_only_manual_research_dispatch_and_narrow_pr_paths(self):
        path=ROOT/".github/workflows/art4k-original-manual-crops.yml"
        text=path.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:",text)
        self.assertIn("pull_request:",text)
        self.assertNotIn("\n  push:",text)
        self.assertIn("concurrency:",text)
        self.assertIn("cancel-in-progress:",text)
        self.assertNotIn("schedule:",text)
        self.assertNotIn("cron:",text)
        self.assertIn("permissions:\n  contents: read",text)
        self.assertIn("timeout-minutes: 10",text)
        self.assertIn("runs-on: ubuntu-latest",text)
        self.assertIn("retention-days: 7",text)
        for target in (
            "tools/art/extract_manual_3d_reference_views.py",
            "tools/art/audit_manual_sparse_landmarks.py",
            "tests.unit.test_extract_manual_3d_reference_views",
            "tests.unit.test_audit_manual_sparse_landmarks",
            "reference/imported/manuals/Uniracers-USA-manual.pdf",
            "art4k-original-1994-manual-four-views",
            "authenticated_crops",
            "source_pdf_sha256",
            "source_git_blob_sha1",
            "source_blob",
            "if-no-files-found: error",
            "PyMuPDF==1.26.4",
            "Pillow==11.3.0",
        ):
            with self.subTest(target=target):
                self.assertIn(target,text)
        self.assertNotIn("secrets.",text)
        self.assertNotIn("pull_request_target:",text)
        self.assertNotIn("contents: write",text)
        self.assertNotIn("git push",text)

    def test_generated_source_artifact_remains_unapproved_and_client_local(self):
        text=(ROOT/"tools/art/MANUAL-3D-CROP-EVIDENCE.md").read_text(encoding="utf-8")
        self.assertIn("Mark original printed 2D landmarks locally",text)
        self.assertIn("not scheduled",text)
        self.assertIn("original manual",text.lower())
        self.assertIn("never",text.lower())


if __name__=="__main__":
    unittest.main()
