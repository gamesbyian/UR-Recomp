import json
import unittest
from pathlib import Path
from tools.check_modern_product_settings_catalog import check_catalog

ROOT = Path(__file__).resolve().parents[2]

class ModernProductSettingsCatalogTest(unittest.TestCase):
    def test_catalog_matches_current_sources(self):
        catalog = json.loads((ROOT / "analysis/modern-product-settings.json").read_text())
        errors = check_catalog(
            catalog,
            (ROOT / "native/product/host_product_state.hpp").read_text(),
            (ROOT / "native/product/host_product_state.cpp").read_text(),
            (ROOT / "native/product/modern_options_menu.h").read_text(),
        )
        self.assertEqual(errors, [])

if __name__ == "__main__":
    unittest.main()
