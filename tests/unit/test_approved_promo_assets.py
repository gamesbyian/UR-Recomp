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
        teaser = (showcase / "build_recruitment_teaser.py").read_text(encoding="utf-8")
        continuous = (showcase / "build_continuous_recruitment_edits.py").read_text(encoding="utf-8")
        three_source = (showcase / "build_three_source_recruitment.py").read_text(encoding="utf-8")
        self.assertIn("graph_paper_trailer_art_direction", blue)
        self.assertNotIn("ImageDraw", blue)
        self.assertIn('aspect="portrait"', flagship)
        self.assertIn('cards["__portrait__"]', flagship)
        self.assertIn('vis=("scale=1080:1920:flags=lanczos"', flagship)
        self.assertNotIn("scale=1080:608:flags=neighbor,pad=1080:1920:0:656:0x08101f", flagship)
        self.assertIn("fontcolor=0x202427", flagship)
        self.assertIn("ianmakesjokes@gmail.com", flagship)
        self.assertIn("blueprint-9x16-portrait-2160x3840.png", upgrade)
        self.assertNotIn("boxblur", upgrade)
        self.assertIn("blueprint-9x16-portrait-2160x3840.png", definitive)
        self.assertNotIn("color=c=0x091421", definitive)
        self.assertIn("approved_visual_assets", teaser)
        self.assertIn("approved_visual_assets", continuous)
        self.assertIn("blueprint-16x9-logo-right.png", three_source)
        self.assertNotIn("color=c=black", three_source)

    def test_historical_trailer_entrypoints_fail_closed_or_use_canonical_art(self):
        showcase = ROOT / "tools/showcase"
        graphpaper = (showcase / "build_graphpaper_recruitment_20261020.py").read_text(encoding="utf-8")
        dynamic = (showcase / "build_flagship_dynamic_course_v2.py").read_text(encoding="utf-8")
        self.assertIn("approved_visual_assets", graphpaper)
        self.assertIn("portrait-art", graphpaper)
        self.assertNotIn("uniracers_graphpaper_logo.jpg", graphpaper)
        self.assertIn("RETIRED_NONCOMPLIANT_PROMO_SOURCE", dynamic)
        self.assertNotIn("ffmpeg", dynamic.lower())

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
