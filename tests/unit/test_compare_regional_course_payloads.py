import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "compare_regional_course_payloads.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("regional_courses", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RegionalCoursePayloadComparisonTests(unittest.TestCase):
    def test_diff_stats(self):
        tool = load_tool()
        stats = tool.diff_stats(b"abcdef", b"abcXdefg")
        self.assertFalse(stats["identical"])
        self.assertEqual(stats["length_delta"], 2)
        self.assertEqual(stats["identical_prefix"], 3)

    def test_actual_changed_course_set(self):
        tool = load_tool()
        report = tool.build_report(
            ROOT / "reference/roms/retail/Uniracers_USA.sfc",
            ROOT / "reference/roms/retail/Unirally_Europe.sfc",
        )
        self.assertEqual(report["changed_stream_count"], 7)
        self.assertEqual(
            report["changed_stream_indices"],
            [4, 16, 20, 26, 27, 35, 36],
        )
        self.assertEqual(
            [row["course_name"] for row in report["courses"]],
            [
                "Switcher",
                "Last One",
                "Jumpover",
                "Down+Up",
                "Highroad",
                "Hairpin Hill",
                "Vertical",
            ],
        )
        by_id = {row["stream_index"]: row for row in report["courses"]}
        self.assertEqual(
            by_id[26]["resource_ids"]["europe"],
            by_id[26]["resource_ids"]["usa"] + [0x22],
        )
        self.assertEqual(
            by_id[36]["resource_ids"]["europe"],
            by_id[36]["resource_ids"]["usa"] + [0x22],
        )


if __name__ == "__main__":
    unittest.main()
