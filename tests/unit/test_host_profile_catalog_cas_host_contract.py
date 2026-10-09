"""Guard every production catalog mutation against stale-process writes."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class CatalogCasHostContract(unittest.TestCase):
    def test_production_catalog_edits_only_use_expected_roster(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("save_host_profile_catalog_file(", host)
        self.assertIn("save_host_profile_catalog_file_if_current(", host)
        self.assertIn("persist_profile_catalog(prior_catalog)", host)
        self.assertIn("persist_profile_catalog(original_catalog)", host)


if __name__ == "__main__":
    unittest.main()
