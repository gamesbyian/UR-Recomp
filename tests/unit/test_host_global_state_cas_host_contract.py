"""QA-02: production must never clobber another process's profile selector."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class GlobalHostStateCasContract(unittest.TestCase):
    def test_all_production_global_state_writes_require_disk_baseline(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("save_host_product_state_file(", host)
        self.assertIn("save_host_product_state_file_if_current(", host)
        self.assertIn("g_product_state_disk_baseline", host)
        self.assertIn("g_product_state_disk_baseline = *loaded.state;", host)
        self.assertIn("g_product_state_disk_baseline = candidate;", host)
        self.assertIn("UR_HOST_STATE SAVE_CONFLICT", host)


if __name__ == "__main__":
    unittest.main()
