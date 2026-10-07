import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "compare_racer_hd_local_stock_contexts.py"

spec = importlib.util.spec_from_file_location("stock_context_delta", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class RacerHdLocalStockContextDeltaTests(unittest.TestCase):
    def test_compare_rgba_classifies_alpha_and_color_changes(self):
        size = module.W * module.H * 4
        left = bytearray(size)
        right = bytearray(size)

        def put(buf, x, y, rgba):
            pos = (y * module.W + x) * 4
            buf[pos:pos + 4] = bytes(rgba)

        put(right, 1, 2, (10, 20, 30, 255))
        put(left, 3, 4, (40, 50, 60, 255))
        put(left, 5, 6, (1, 2, 3, 255))
        put(right, 5, 6, (9, 8, 7, 255))

        delta = module.compare_rgba(bytes(left), bytes(right))
        self.assertEqual(delta["changed_pixel_count"], 3)
        self.assertEqual(delta["changed_bbox_inclusive"], [1, 2, 5, 6])
        self.assertEqual(delta["alpha_added_pixels"], [[1, 2]])
        self.assertEqual(delta["alpha_removed_pixels"], [[3, 4]])
        self.assertEqual(delta["color_only_changed_pixels"], [[5, 6]])

    def test_identical_rasters_have_empty_delta(self):
        payload = bytes(module.W * module.H * 4)
        delta = module.compare_rgba(payload, payload)
        self.assertEqual(delta["changed_pixel_count"], 0)
        self.assertIsNone(delta["changed_bbox_inclusive"])
        self.assertEqual(delta["alpha_added_count"], 0)
        self.assertEqual(delta["alpha_removed_count"], 0)
        self.assertEqual(delta["color_only_changed_count"], 0)

    def test_context_normalizes_hex_and_player_scope(self):
        context = module._context(
            player="p2",
            primary="0578",
            companion="0ec3",
            selector=0,
            gate="0001",
        )
        self.assertEqual(context["p1_primary"], "0x0000")
        self.assertEqual(context["p2_primary"], "0x0578")
        self.assertEqual(context["p2_companion"], "0x0EC3")
        self.assertEqual(context["p2_gate"], "0x0001")


if __name__ == "__main__":
    unittest.main()
