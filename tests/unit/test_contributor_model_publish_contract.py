"""Keep Pages 3D publishing tied to exact-current-source, checked GLB exports."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ContributorModelPublishTests(unittest.TestCase):
    def test_contributor_publish_regenerates_five_source_verified_poses(self):
        w = (ROOT / ".github/workflows/windows-visual-atlas-site.yml").read_text(encoding="utf-8")
        gate = "(github.event_name == 'push' && steps.gallery-change.outputs.publish == 'true')"
        # Dependency installation, five-pose generation and receipt/measurement
        # staging must all run on the same authorized contributor publish.
        self.assertEqual(w.count(gate), 3)
        self.assertIn('tools/art/candidates/unicycle_shared_rig.scad', w)
        self.assertIn('tools/art/export_articulated_unicycle.py', w)
        self.assertIn('tools/art/model-review/stage_pages.py', w)
        self.assertIn('tools/art/prepare_model_review_measurement_sidecar.py', w)
        self.assertIn('for pose in upright pedal wheelie stunt bank; do', w)
        self.assertIn('--source-commit "$source_commit"', w)
        self.assertIn('tools/contributor_gallery/stage.py --site', w)
        self.assertIn('needs.assemble-site.outputs.contributor_publish', w)
        self.assertIn('uses: actions/deploy-pages@v4', w)

    def test_recruitment_models_are_experimental(self):
        stage = (ROOT / "tools/art/model-review/stage_pages.py").read_text(encoding="utf-8")
        self.assertIn('original_character_likeness_approved', stage)
        self.assertIn('shipping_art_approved', stage)
        self.assertIn('glb_sha256', stage)
        model_page = (ROOT / "tools/contributor_gallery/three-d.html").read_text(encoding="utf-8")
        self.assertIn('Uniracers', model_page)
        self.assertIn('manifest.json', model_page)
        self.assertIn('original 1994', model_page)
        self.assertIn('mailto:ianmakesjokes@gmail.com', model_page)


if __name__ == "__main__":
    unittest.main()
