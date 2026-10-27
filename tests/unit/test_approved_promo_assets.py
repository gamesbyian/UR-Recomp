"""Guard the owner-approved promotional video asset contract."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/showcase/graph_paper_trailer_art_direction.py"
spec = importlib.util.spec_from_file_location("approved_promo", SCRIPT)
promo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promo)


class ApprovedPromoTests(unittest.TestCase):
    def test_importing_source_manifest_never_requires_optional_pillow(self):
        # CI's dependency-free tooling run must be able to inspect SOURCES
        # even on hosts without Pillow. Rendering still requires real Pillow.
        from builtins import __import__ as real_import

        def absent_pillow(name, *args, **kwargs):
            if name == "PIL" or name.startswith("PIL."):
                raise ModuleNotFoundError("Pillow deliberately absent in unit CI")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=absent_pillow):
            isolated = importlib.util.spec_from_file_location(
                "approved_promo_without_pillow", SCRIPT)
            module = importlib.util.module_from_spec(isolated)
            isolated.loader.exec_module(module)
        self.assertEqual(module.SOURCES["portrait"],
                         "blueprint-9x16-portrait-2160x3840.png")

    def test_all_known_exporters_reference_approved_sources(self):
        showcase = ROOT / "tools/showcase"
        blue = (showcase / "blue_trailer_art_direction.py").read_text(encoding="utf-8")
        flagship = (showcase / "build_flagship_recruitment_20261019.py").read_text(encoding="utf-8")
        upgrade = (showcase / "upgrade_flagship_vertical_20261019.py").read_text(encoding="utf-8")
        definitive = (showcase / "build_definitive_recruitment.py").read_text(encoding="utf-8")
        self.assertIn("graph_paper_trailer_art_direction", blue)
        self.assertNotIn("ImageDraw", blue)
        self.assertIn('aspect="portrait"', flagship)
        self.assertIn('cards["__portrait__"]', flagship)
        self.assertIn("blueprint-9x16-portrait-2160x3840.png", upgrade)
        self.assertNotIn("boxblur", upgrade)
        self.assertIn("blueprint-9x16-portrait-2160x3840.png", definitive)
        self.assertNotIn("color=c=0x091421", definitive)

    def test_portrait_only_approved_plate(self):
        self.assertEqual(promo.SOURCES["portrait"],
                         "blueprint-9x16-portrait-2160x3840.png")
        self.assertEqual(promo.SIZE["portrait"], (1080, 1920))

    def test_all_landscape_variants_are_canonical(self):
        for key, filename in promo.SOURCES.items():
            with self.subTest(key=key):
                self.assertTrue((promo.APPROVED / filename).is_file())

    def test_legacy_graph_paper_drawing_is_retired(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for legacy in ("ImageDraw", "ink_overlay(", "def footer(", "graphpaper-final/cards"):
            self.assertNotIn(legacy, source)


if __name__ == "__main__":
    unittest.main()
