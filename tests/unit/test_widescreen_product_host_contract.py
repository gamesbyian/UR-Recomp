import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
HOOK = ROOT / "tools" / "apply_native_widescreen_hook.py"


class WidescreenProductHostContractTests(unittest.TestCase):
    def test_shipping_product_disables_guest_widescreen_lane(self):
        host = HOST.read_text(encoding="utf-8")
        start = host.index("void synchronize_widescreen_provider_selector()")
        end = host.index("\nbool authentic_16x9_view_enabled()", start)
        body = host[start:end]
        self.assertIn('URRECOMP_WS_GUEST_LANE", "0"', body)
        self.assertIn('if (std::getenv("URRECOMP_WS_MARGIN")) return;', body)
        self.assertIn('const char* explicit_view = std::getenv("URRECOMP_WS_VIEW");', body)

    def test_hook_guest_lane_zero_preserves_stock_guest_ring(self):
        hook = HOOK.read_text(encoding="utf-8")
        self.assertIn("URRECOMP_WS_GUEST_LANE=0 keeps the second pass", hook)
        self.assertIn(
            'ur_ws_native_guest_lane_cache = (s && strcmp(s, "0") == 0) ? 0 : 1;',
            hook,
        )
        self.assertIn("if (ur_ws_native_guest_lane()) {", hook)


if __name__ == "__main__":
    unittest.main()
