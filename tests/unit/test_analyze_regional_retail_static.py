import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "analyze_regional_retail_static.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("regional_static", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RegionalRetailStaticAnalysisTests(unittest.TestCase):
    def test_verified_retail_inventory(self):
        tool = load_tool()
        report = tool.build_report(ROOT)

        self.assertEqual(report["roms"]["usa"]["header_title"], "UNIRACERS")
        self.assertEqual(report["roms"]["europe"]["header_title"], "UNIRALLY")
        self.assertEqual(report["roms"]["usa"]["region"], 0x01)
        self.assertEqual(report["roms"]["europe"]["region"], 0x02)
        self.assertEqual(report["roms"]["usa"]["reset_vector"], 0x8858)
        self.assertEqual(report["roms"]["europe"]["reset_vector"], 0x8858)

        self.assertEqual(report["rnc"]["usa_count"], 45)
        self.assertEqual(report["rnc"]["europe_count"], 45)
        self.assertEqual(report["rnc"]["byte_identical_count"], 38)
        self.assertEqual(
            report["rnc"]["changed_stream_indices"],
            [4, 16, 20, 26, 27, 35, 36],
        )
        self.assertTrue(
            report["known_resource_catalog_crosscheck"]["matches_rnc_scan"]
        )

        changed = {
            item["stream_index"]: item for item in report["rnc"]["changed_streams"]
        }
        expected_names = {
            4: "Switcher",
            16: "Last One",
            20: "Jumpover",
            26: "Down+Up",
            27: "Highroad",
            35: "Hairpin Hill",
            36: "Vertical",
        }
        self.assertEqual(
            {idx: item["course"]["name"] for idx, item in changed.items()},
            expected_names,
        )
        self.assertEqual(
            changed[26]["resource_delta"], {"kind": "append", "values": [34]}
        )
        self.assertEqual(
            changed[36]["resource_delta"], {"kind": "append", "values": [34]}
        )
        self.assertEqual(
            changed[4]["known_header_delta"]["spawn_or_landmark_a"],
            {"before": [99, 26], "after": [99, 22]},
        )

    def test_markdown_is_bounded_and_explicit(self):
        tool = load_tool()
        report = tool.build_report(ROOT)
        text = tool.markdown(report)
        self.assertIn("Static differences are candidates only", text)
        self.assertIn("38/45", text)
        self.assertIn("Switcher", text)
        self.assertIn("Down+Up", text)
        self.assertIn("Vertical", text)
        self.assertIn("Candidate printable-string differences", text)


if __name__ == "__main__":
    unittest.main()
