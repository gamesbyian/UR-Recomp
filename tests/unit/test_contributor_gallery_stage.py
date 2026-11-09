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
            self.assertEqual(len(report), 8)
            self.assertTrue((folder/"contributors/index.html").is_file())
            self.assertFalse((folder/"contributors/images/unirally-box-art-3x.png").exists())
            self.assertFalse((folder/"contributors/images/uniracers-box-art-3x.png").exists())
            self.assertTrue(all(item["bytes"] > 0 for item in report.values()))
            parser = ImageSources()
            parser.feed((folder / "contributors/index.html").read_text(encoding="utf-8"))
            self.assertEqual(len(parser.images), 8)
            self.assertTrue(all(isinstance(src, str) and src.startswith("images/") for src in parser.images))
            for src in parser.images:
                self.assertTrue((folder / "contributors" / src).is_file(), src)
            with self.assertRaises(ValueError):
                MOD.stage(folder)
if __name__ == "__main__":
    unittest.main()
