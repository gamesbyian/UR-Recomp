import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class FinalWindowFilteringBindingTests(unittest.TestCase):
    def setUp(self):
        self.source = HOST.read_text(encoding="utf-8")

    def test_modern_after_config_binds_product_filter_policy(self):
        start = self.source.index(
            'extern "C" void ur_uniracers_modern_after_config(void)'
        )
        end = self.source.index(
            'extern "C" int ur_uniracers_modern_native_widescreen_enabled',
            start,
        )
        body = self.source[start:end]
        self.assertIn("if (modern_mode())", body)
        self.assertIn("default_final_window_filter()", body)
        self.assertIn("snesrecomp_desktop_get_linear_filtering()", body)
        self.assertIn("snesrecomp_desktop_set_linear_filtering(linear)", body)

    def test_binding_is_idempotent_and_authentic_is_inert(self):
        start = self.source.index(
            'extern "C" void ur_uniracers_modern_after_config(void)'
        )
        end = self.source.index(
            'extern "C" int ur_uniracers_modern_native_widescreen_enabled',
            start,
        )
        body = self.source[start:end]
        self.assertIn(
            "if (snesrecomp_desktop_get_linear_filtering() != linear)",
            body,
        )
        # The setter lives only inside the Modern guard. Authentic therefore
        # preserves the framework/config-owned final-window treatment.
        guard = body.index("if (modern_mode())")
        setter = body.index("snesrecomp_desktop_set_linear_filtering")
        self.assertGreater(setter, guard)


if __name__ == "__main__":
    unittest.main()
