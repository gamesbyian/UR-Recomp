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

    def test_region_partition_preserves_exact_materialization_boundaries(self):
        tool = load_tool()
        # One full coarse table, one 32-byte fine record, and a terminated list.
        data = bytearray(0x800F + 32 + 3)
        cursor = 0x800F + 32
        data[cursor:] = b"\x01\x24\xff"
        parsed = {
            "resource_cursor_initial": cursor,
            "resource_terminator_offset": cursor + 2,
        }
        regions = tool.regions(bytes(data), parsed)
        self.assertEqual(len(regions["coarse_table"]), 0x8000)
        self.assertEqual(len(regions["fine_record_region"]), 32)
        self.assertEqual(regions["resource_list"], b"\x01\x24\xff")
        self.assertEqual(sum(map(len, regions.values())), len(data))

    def test_region_partition_rejects_shifted_or_truncated_course(self):
        tool = load_tool()
        data = bytearray(0x800F + 33 + 3)
        cursor = 0x800F + 33
        data[cursor:] = b"\x01\x24\xff"
        parsed = {
            "resource_cursor_initial": cursor,
            "resource_terminator_offset": cursor + 2,
        }
        with self.assertRaisesRegex(ValueError, "32-byte aligned"):
            tool.regions(bytes(data), parsed)
        with self.assertRaisesRegex(ValueError, "truncated"):
            tool.regions(bytes(data[:0x800E]), parsed)
        with self.assertRaisesRegex(ValueError, "outside course fine-record"):
            tool.regions(bytes(data), {**parsed, "resource_cursor_initial": 0x800E})
        with self.assertRaisesRegex(ValueError, "outside course resource list"):
            tool.regions(bytes(data), {**parsed, "resource_terminator_offset": len(data)})
        damaged = bytes(data[:-1] + b"\x00")
        with self.assertRaisesRegex(ValueError, "not FF"):
            tool.regions(damaged, parsed)

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
