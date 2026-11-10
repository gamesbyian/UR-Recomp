"""Keep Pages 3D publishing tied to exact-current-source, checked GLB exports."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ContributorModelPublishTests(unittest.TestCase):
    def test_only_changed_model_sources_regenerate_five_verified_poses(self):
        w = (ROOT / ".github/workflows/windows-visual-atlas-site.yml").read_text(encoding="utf-8")
        # A button or page styling change copies HTML from exact main into
        # the previous site artifact. It cannot invalidate model/atlas bytes.
        self.assertIn("gh run download", w)
        self.assertIn("publish_incremental.py plan", w)
        self.assertIn("publish_incremental.py overlay", w)
        self.assertIn("if: steps.plan.outputs.atlas == 'true'", w)
        self.assertIn("if: steps.plan.outputs.gallery == 'true'", w)
        self.assertIn("if: steps.plan.outputs.html == 'true'", w)
        self.assertEqual(w.count("if: steps.plan.outputs.model == 'true'"), 2)
        self.assertNotIn("gallery-change.outputs.publish", w)
        self.assertIn("model-placeholder", w)
        self.assertIn("tools/art/candidates/unicycle_shared_rig.scad", w)
        self.assertIn("tools/art/export_articulated_unicycle.py", w)
        self.assertIn("tools/art/model-review/stage_pages.py", w)
        self.assertIn("tools/art/prepare_model_review_measurement_sidecar.py", w)
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
