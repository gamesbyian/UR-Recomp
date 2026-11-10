"""Targeted no-regeneration contract for contributor Pages publication."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "incremental_pages", ROOT / "tools/contributor_gallery/publish_incremental.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IncrementalPublishTests(unittest.TestCase):
    def test_button_colour_change_is_html_only(self):
        p = MODULE.plan_changes(["tools/contributor_gallery/index.html"])
        self.assertEqual(p, {"atlas": False, "gallery": False, "model": False,
                             "html": True, "model_page": False, "publish": True})

    def test_all_four_page_edits_are_html_only(self):
        p = MODULE.plan_changes(list(MODULE.HTML_ROUTES))
        self.assertTrue(p["publish"] and p["html"])
        self.assertFalse(p["atlas"] or p["gallery"] or p["model"])

    def test_model_review_page_edits_reuse_existing_glbs(self):
        p = MODULE.plan_changes(["tools/art/model-review/index.html", "tools/art/model-review/index_overlay.mjs"])
        self.assertTrue(p["model_page"] and p["publish"])
        self.assertFalse(p["model"] or p["atlas"] or p["gallery"])

    def test_gallery_asset_changes_do_not_trigger_model(self):
        p = MODULE.plan_changes([
            "assets/branding/concepts/regional-wordmark-concept-01.png",
            "tools/contributor_gallery/source/uniracers_graphpaper_logo.jpg",
        ])
        self.assertTrue(p["gallery"])
        self.assertFalse(p["model"] or p["atlas"])

    def test_model_and_atlas_rebuild_only_for_their_own_inputs(self):
        model = MODULE.plan_changes(["tools/art/candidates/unicycle_shared_rig.scad"])
        self.assertTrue(model["model"])
        self.assertFalse(model["atlas"] or model["gallery"])
        atlas = MODULE.plan_changes(["tools/visual_atlas_web/atlas.css"])
        self.assertTrue(atlas["atlas"])
        self.assertFalse(atlas["model"] or atlas["gallery"])

    def test_docs_and_publisher_code_do_not_republish(self):
        p = MODULE.plan_changes([
            "docs/contributors/README.md",
            "tools/contributor_gallery/publish_incremental.py",
            ".github/workflows/windows-visual-atlas-site.yml",
        ])
        self.assertFalse(any(p.values()))

    def test_overlays_only_changed_html_preserving_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            target = site / "contributors/index.html"
            target.parent.mkdir()
            target.write_text("old")
            untouched = site / "model-review/pose.glb"
            untouched.parent.mkdir()
            untouched.write_bytes(b"preserve exact model bytes")
            copied = MODULE.overlay_html(site, ["tools/contributor_gallery/index.html"])
            self.assertEqual(copied, ["contributors/index.html"])
            self.assertEqual(target.read_bytes(),
                             (ROOT / "tools/contributor_gallery/index.html").read_bytes())
            self.assertEqual(untouched.read_bytes(), b"preserve exact model bytes")

    def test_model_placeholder_preserves_reference_materials(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"
            old = site / "model-review"
            old.mkdir(parents=True)
            (old / "manifest.json").write_text('{"schema":"ur-racer-model-review/1","model_url":"assets/p.glb"}')
            (old / "original-mesen24").mkdir()
            (old / "original-mesen24/source-poses.json").write_text("proof")
            (old / "assets").mkdir()
            (old / "assets/old.glb").write_bytes(b"old model")
            backup = Path(tmp) / "saved-model"
            MODULE.prepare_model_placeholder(site, backup)
            self.assertTrue((backup / "assets/old.glb").exists())
            self.assertEqual((old / "original-mesen24/source-poses.json").read_text(), "proof")
            self.assertIsNone(__import__("json").loads((old / "manifest.json").read_text())["model_url"])

    def test_refuses_missing_or_redirected_staged_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                MODULE.overlay_html(Path(tmp), ["tools/contributor_gallery/index.html"])


if __name__ == "__main__":
    unittest.main()
