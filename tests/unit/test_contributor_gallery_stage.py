"""Offline gate: contributor gallery packaging without network, ROM, or box art."""
import importlib.util
from pathlib import Path
from html.parser import HTMLParser
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("stage_contributor_gallery", ROOT / "tools/contributor_gallery/stage.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
class ImageSources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs).get("src"))


class ContributorGalleryTests(unittest.TestCase):
    def test_stages_only_approved_source_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            report = MOD.stage(folder)
            self.assertEqual(len(report), 12)
            self.assertTrue((folder/"contributors/index.html").is_file())
            self.assertTrue((folder/"contributors/references/index.html").is_file())
            self.assertTrue((folder/"contributors/3d/index.html").is_file())
            self.assertTrue((folder/"contributors/3d/models/unicycle_shared_rig.scad").is_file())
            source_dir = ROOT / "media/showcase/art-reconstruction/2026-11-09/title-screen-racer"
            racer_names = (
                "title-screen-racer-3x-upscale.png",
                "racer-contour-overlay-wide.png",
                "racer-contour-overlay-close.png",
                "racer-contour-overlay-axle-detail.png",
            )
            for name in racer_names:
                full_original = source_dir / name
                preview_path = folder / "contributors/3d/previews" / name
                self.assertTrue(preview_path.is_file(), name)
                self.assertLess(preview_path.stat().st_size, full_original.stat().st_size, name)
                self.assertFalse((folder / "contributors/3d/images" / name).exists(), name)

            box_dir = ROOT / "media/showcase/art-reconstruction/2026-11-10/box-art-wheel-contours"
            box_names = (
                "uniracers-box-art-wheel-contour-study.jpg",
                "unirally-box-art-wheel-contour-study.jpg",
            )
            for name in box_names:
                staged = folder / "contributors/3d/box-art" / name
                self.assertTrue(staged.is_file(), name)
                self.assertEqual((box_dir / name).read_bytes(), staged.read_bytes(), name)
            self.assertFalse((folder / "contributors/3d/box-art/Uniracers_box_art_3x~2.jpg").exists())

            self.assertEqual(
                (ROOT / "tools/art/candidates/unicycle_shared_rig.scad").read_bytes(),
                (folder/"contributors/3d/models/unicycle_shared_rig.scad").read_bytes()
            )
            self.assertTrue((folder/"contributors/images/blueprint-16x9-logo-left.png").is_file())
            self.assertTrue((folder/"contributors/images/blueprint-4x3-logo-left.png").is_file())
            self.assertTrue((folder/"contributors/images/uniracers_graphpaper_logo.jpg").is_file())
            self.assertTrue((folder/"contributors/images/uniracers_track_unicycle.jpg").is_file())
            self.assertFalse((folder/"contributors/images/unirally-box-art-3x.png").exists())
            self.assertFalse((folder/"contributors/images/uniracers-box-art-3x.png").exists())
            self.assertTrue(all(item["bytes"] > 0 for item in report.values()))
            parser = ImageSources()
            parser.feed((folder / "contributors/references/index.html").read_text(encoding="utf-8"))
            self.assertEqual(len(parser.images), 8)
            self.assertTrue(all(isinstance(src, str) and src.startswith("../images/") for src in parser.images))
            for src in parser.images:
                self.assertTrue((folder / "contributors/references" / src).is_file(), src)
            home = (folder/"contributors/index.html").read_text(encoding="utf-8")
            self.assertIn("One wheel.<br>A bigger future.", home)
            self.assertIn('background-attachment:fixed', home)
            self.assertIn('class="sketch-logo"', home)
            self.assertIn('class="bottom"', home)
            self.assertIn('class="track"', home)
            self.assertIn('images/uniracers_graphpaper_logo.jpg', home)
            self.assertIn('images/uniracers_track_unicycle.jpg', home)
            self.assertNotIn('class="hero-image"', home)
            self.assertNotIn('<picture>', home)
            home_parser = ImageSources()
            home_parser.feed(home)
            self.assertEqual(home_parser.images, [
                "images/uniracers_graphpaper_logo.jpg",
                "images/uniracers_track_unicycle.jpg",
            ])
            for src in home_parser.images:
                self.assertTrue((folder / "contributors" / src).is_file(), src)
            self.assertIn("position:fixed", home)
            self.assertIn("./references/", home)
            self.assertIn('href="./3d/">View model &amp; downloads', home)
            # Every volunteer path has both public email and GitHub intake;
            # none requires a GitHub account to make contact.
            self.assertEqual(home.count("Use GitHub instead"), 5)
            self.assertGreaterEqual(home.count("mailto:ianmakesjokes@gmail.com"), 5)

            three_d = (folder/"contributors/3d/index.html").read_text(encoding="utf-8")
            self.assertIn('../../model-review/', three_d)
            self.assertIn('../../model-review/visual-review.html', three_d)
            self.assertIn('./models/unicycle_shared_rig.scad', three_d)
            self.assertIn('manifest.json', three_d)
            self.assertIn("mailto:ianmakesjokes@gmail.com", three_d)
            self.assertIn("Use GitHub instead", three_d)
            for name in racer_names:
                self.assertIn('src="previews/' + name + '"', three_d)
                self.assertIn(
                    'https://github.com/gamesbyian/UR-Recomp/blob/main/media/showcase/art-reconstruction/2026-11-09/title-screen-racer/' + name,
                    three_d,
                )
            for name in box_names:
                self.assertIn('src="box-art/' + name + '"', three_d)
                self.assertIn('https://github.com/gamesbyian/UR-Recomp/blob/main/media/showcase/art-reconstruction/2026-11-10/box-art-wheel-contours/' + name, three_d)
            self.assertIn("Additional wheel and fork details", three_d)
            self.assertIn("artist's interpretation", three_d)
            self.assertIn("non-generatively downscaled previews", three_d)
            self.assertIn('No hosted GLB is currently listed', three_d)
            for role in ("3D artists", "Lettering &amp; language", "Developers &amp; AI operators", "Future playtesters"):
                self.assertIn(role, home)
            self.assertIn("Three new regional styling concepts", (folder/"contributors/references/index.html").read_text())
            with self.assertRaises(ValueError):
                MOD.stage(folder)
if __name__ == "__main__":
    unittest.main()
