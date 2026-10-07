import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "compare_retail_frontend.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("retail_frontend", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RetailFrontendComparisonTests(unittest.TestCase):
    def test_existing_dir_comparison(self):
        tool = load_tool()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            usa = root / "usa"
            eur = root / "eur"
            usa.mkdir()
            eur.mkdir()

            same = bytes([0, 0, 0, 0] * 4)
            changed = bytearray(same)
            changed[4:8] = bytes([1, 2, 3, 4])

            (usa / "same.fb.bgrx").write_bytes(same)
            (eur / "same.fb.bgrx").write_bytes(same)
            (usa / "changed.fb.bgrx").write_bytes(same)
            (eur / "changed.fb.bgrx").write_bytes(bytes(changed))

            report = tool.compare_existing_dirs(
                usa, eur, ["same", "changed", "missing"]
            )
            self.assertEqual(report["expected"], 3)
            self.assertEqual(report["both_present"], 2)
            self.assertEqual(report["frame_differences"], 1)
            rows = {row["checkpoint"]: row for row in report["checkpoints"]}
            self.assertEqual(rows["same"]["framebuffer"]["changed_pixels"], 0)
            self.assertEqual(rows["changed"]["framebuffer"]["changed_pixels"], 1)
            self.assertFalse(rows["missing"]["usa_present"])
            self.assertFalse(rows["missing"]["europe_present"])

    def test_case_catalog_uses_semantic_routes(self):
        tool = load_tool()
        self.assertIn("title-motion", tool.CASES)
        self.assertFalse(tool.CASES["title-motion"]["default"])
        self.assertEqual(
            tool.CASES["title-motion"]["checkpoints"],
            ["title-motion-000", "title-motion-180"],
        )
        self.assertIn("title-transition", tool.CASES)
        self.assertEqual(
            tool.CASES["title-transition"]["checkpoints"],
            [
                "boot-300",
                "boot-360",
                "boot-420",
                "main-menu-first",
                "main-menu-settled",
            ],
        )
        self.assertIn("startup-main", tool.CASES)
        self.assertEqual(
            tool.CASES["startup-main"]["checkpoints"],
            ["ui-startup-main-menu"],
        )
        for case in tool.CASES.values():
            self.assertTrue((ROOT / case["script"]).is_file())
            self.assertTrue(case["checkpoints"])
        default_cases = sorted(
            name
            for name, case in tool.CASES.items()
            if case.get("default", True)
        )
        self.assertNotIn("title-motion", default_cases)
        self.assertIn("title-transition", default_cases)


if __name__ == "__main__":
    unittest.main()
