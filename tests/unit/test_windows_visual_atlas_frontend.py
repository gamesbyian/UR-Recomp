"""ROM-free UI contracts: real controls, build outputs and preserved concept authorities."""
from __future__ import annotations

from html.parser import HTMLParser
import re
import struct
import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools import windows_visual_atlas as atlas


class IDs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.identities: set[str] = set()
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id" and value:
                if value in self.identities:
                    raise ValueError("Duplicate element ID: " + value)
                self.identities.add(value)


class WindowsAtlasFrontendTests(unittest.TestCase):
    def test_the_actual_static_assembler_contains_every_interface_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "site"
            snapshot = atlas.build(atlas.load_catalog(), dest, None, None)
            self.assertEqual(len(snapshot["entries"]), 199)
            for filename in ("index.html", "atlas.js", "atlas.css", "tube-header.svg"):
                self.assertTrue((dest / filename).is_file(), filename)
            self.assertEqual(snapshot["counts"]["captured"], 0)
            self.assertNotIn("mockup", (dest / "atlas.json").read_text())
            self.assertFalse((dest / "design").exists())

    def test_every_static_javascript_dom_target_exists(self):
        html = (atlas.WEB / "index.html").read_text(encoding="utf-8")
        js = (atlas.WEB / "atlas.js").read_text(encoding="utf-8")
        parsed = IDs()
        parsed.feed(html)
        missing = set(re.findall(r'\$\("([a-z][a-z0-9-]+)"\)', js)) - parsed.identities
        self.assertFalse(missing, f"JS referenced absent controls: {missing}")
        essentials = {
            "search", "mode", "family", "status", "evidence", "sort",
            "view-list", "view-grid", "gallery", "detail", "detail-title",
            "image-stage", "copy-ref", "copy-link", "open-source",
            "prev", "next", "zoom", "selection-copy", "selection-clear",
        }
        self.assertFalse(essentials - parsed.identities)
        self.assertIn('aria-labelledby="detail-title"', html)
        self.assertIn('role="status"', html)

    def test_mobile_first_layout_and_source_grounded_actions(self):
        css = (atlas.WEB / "atlas.css").read_text(encoding="utf-8")
        js = (atlas.WEB / "atlas.js").read_text(encoding="utf-8")
        self.assertIn("@media(min-width:620px)", css)
        self.assertIn("@media(min-width:1000px)", css)
        self.assertIn("min-width:0", css)
        self.assertIn("env(safe-area-inset-bottom)", css)
        self.assertIn('source_inventory?.path', js)
        self.assertIn('actual_sdl_final_drawable', js)
        self.assertIn('e.status==="captured"', js)
        self.assertIn('NO Windows capture', js)
        self.assertIn("selected=new Set()", js)
        self.assertIn("navigator.clipboard", js)
        self.assertIn("history.pushState", js)

    def test_original_revised_mockups_preserved_and_not_used_as_capture_proof(self):
        folder = atlas.ROOT / "design/visual-atlas/mockups"
        for name, dimensions in {
            "2026-10-23-desktop-gallery.png": (1448, 1086),
            "2026-10-23-desktop-detail.png": (1448, 1086),
            "2026-10-23-mobile-gallery.png": (941, 1672),
            "2026-10-23-mobile-detail.png": (941, 1672),
        }.items():
            data = (folder / name).read_bytes()
            self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"), name)
            self.assertGreater(len(data), 2_000_000, name)
            self.assertEqual(struct.unpack(">II", data[16:24]), dimensions)
        self.assertIn("not native windows captures", (folder / "README.md").read_text().lower())

    def test_header_svg_is_small_and_has_cylindrical_track_and_contacting_wheel(self):
        svg_path = atlas.WEB / "tube-header.svg"
        self.assertLess(svg_path.stat().st_size, 8000)
        tree = ET.parse(svg_path)
        root = tree.getroot()
        self.assertEqual(root.attrib.get("viewBox"), "0 0 392 164")
        self.assertIn("cylindrical", svg_path.read_text().lower())
        self.assertIn("tyre", svg_path.read_text().lower())


if __name__ == "__main__":
    unittest.main()
