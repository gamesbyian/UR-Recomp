import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PATCH = ROOT / "tools" / "patches" / "snesrecomp-live-linear-filtering.patch"


class LiveLinearFilteringPatchTests(unittest.TestCase):
    def test_patch_exposes_live_filter_api_and_reconfigures_renderer(self):
        text = PATCH.read_text(encoding="utf-8")
        self.assertIn("snesrecomp_desktop_set_linear_filtering", text)
        self.assertIn("snesrecomp_desktop_get_linear_filtering", text)
        self.assertIn("g_config.linear_filtering = enabled != 0;", text)
        self.assertIn("g_renderer_funcs.Reconfigure", text)
        self.assertIn("g_renderer_funcs.Reconfigure();", text)
        self.assertNotIn("Rtl", text)
        self.assertNotIn("g_ram", text)

    def test_patch_is_registered_after_display_mode_capability(self):
        manifest = json.loads(
            (ROOT / "tools" / "toolchain-entries" / "snesrecomp.json").read_text(
                encoding="utf-8"
            )
        )
        paths = [entry["path"] for entry in manifest["patches"]]
        display = paths.index("tools/patches/snesrecomp-display-mode-capability.patch")
        filtering = paths.index(
            "tools/patches/snesrecomp-live-linear-filtering.patch"
        )
        self.assertEqual(filtering, display + 1)


if __name__ == "__main__":
    unittest.main()
