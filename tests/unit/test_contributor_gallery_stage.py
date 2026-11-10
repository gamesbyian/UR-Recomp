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
            self.assertIn("One wheel. A bigger future.", home)
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
            self.assertIn("images/blueprint-16x9-logo-left.png", home)
            self.assertIn("images/blueprint-4x3-logo-left.png", home)
            for role in ("3D artists", "Lettering &amp; language", "Developers &amp; AI operators", "Future playtesters"):
                self.assertIn(role, home)
            self.assertIn("Three new regional styling concepts", (folder/"contributors/references/index.html").read_text())
            with self.assertRaises(ValueError):
                MOD.stage(folder)
if __name__ == "__main__":
    unittest.main()
