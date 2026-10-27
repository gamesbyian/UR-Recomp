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
