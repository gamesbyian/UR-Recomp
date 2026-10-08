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
        # Test terminator guards on a *validly aligned* candidate.
        aligned = bytearray(0x800F + 32 + 3)
        aligned_cursor = 0x800F + 32
        aligned[aligned_cursor:] = b"\x01\x24\xff"
        aligned_parsed = {
            "resource_cursor_initial": aligned_cursor,
            "resource_terminator_offset": aligned_cursor + 2,
        }
        with self.assertRaisesRegex(ValueError, "outside course resource list"):
            tool.regions(
                bytes(aligned),
                {**aligned_parsed, "resource_terminator_offset": len(aligned)},
            )
        aligned[-1] = 0
        with self.assertRaisesRegex(ValueError, "not FF"):
            tool.regions(bytes(aligned), aligned_parsed)

    @staticmethod
    def _spatial_payload(*, swapped=False, changed_word=None):
        # Two 32-byte fine records; the second is used by two sectors.
        coarse = [0] * 16384
        coarse[1] = coarse[2] = 1
        zero = [0] * 16
        one = [0] * 16
        one[3] = 0x0002 if changed_word is None else changed_word
        if swapped:
            zero, one = one, zero
            coarse = [1 - value for value in coarse]
        cursor = 0x800F + 64
        header = bytearray(15)
        header[11:13] = cursor.to_bytes(2, "little")
        header[13:15] = b"\x20\x20"
        table = b"".join(value.to_bytes(2, "little") for value in coarse)
        fine = b"".join(value.to_bytes(2, "little") for value in zero + one)
        return bytes(header) + table + fine + b"\x01\xff"

    def test_effective_placement_ignores_fine_record_renumbering(self):
        tool = load_tool()
        usa = self._spatial_payload()
        europe = self._spatial_payload(swapped=True)
        result = tool.effective_surface_delta(
            usa, europe, tool.parse_course_resource_list(usa),
            tool.parse_course_resource_list(europe),
        )
        self.assertTrue(result["comparable"])
        self.assertEqual(result["raw_coarse_reference_id_changes"], 16384)
        self.assertEqual(result["changed_world_cells"], 0)
        self.assertEqual(result["changed_world_cell_bounds"], None)

    def test_effective_placement_expands_shared_record_to_world_cells(self):
        tool = load_tool()
        usa = self._spatial_payload()
        europe = self._spatial_payload(changed_word=0x0004)
        result = tool.effective_surface_delta(
            usa, europe, tool.parse_course_resource_list(usa),
            tool.parse_course_resource_list(europe),
        )
        self.assertEqual(result["raw_coarse_reference_id_changes"], 0)
        self.assertEqual(result["changed_world_sectors"], 2)
        self.assertEqual(result["changed_world_cells"], 2)
        self.assertEqual(result["changed_c000_selectors"], 2)
        self.assertEqual(result["changed_unclassified_upper_word_bits"], 0)
        self.assertEqual(result["first_12_changed_cells"][0]["world_cell_origin"], [112, 0])
        self.assertEqual(result["first_12_changed_cells"][1]["world_cell_origin"], [176, 0])

    def test_effective_placement_distinguishes_upper_word_bits_from_slots(self):
        tool = load_tool()
        usa = self._spatial_payload()
        europe = self._spatial_payload(changed_word=0x0402)
        result = tool.effective_surface_delta(
            usa, europe, tool.parse_course_resource_list(usa),
            tool.parse_course_resource_list(europe),
        )
        self.assertEqual(result["changed_world_cells"], 2)
        self.assertEqual(result["changed_c000_selectors"], 0)
        self.assertEqual(result["changed_unclassified_upper_word_bits"], 2)

    def test_effective_placement_rejects_invalid_coarse_record_reference(self):
        tool = load_tool()
        usa = bytearray(self._spatial_payload())
        usa[15:17] = b"\x02\x00"
        europe = self._spatial_payload()
        with self.assertRaisesRegex(ValueError, "outside its fine-record table"):
            tool.effective_surface_delta(
                bytes(usa), europe, tool.parse_course_resource_list(bytes(usa)),
                tool.parse_course_resource_list(europe),
            )

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
        # Exercise the full seven-course ROM-derived spatial path, not just
        # artificial region permutations. No semantic change count is assumed:
        # an extra resource need not alter an already-placed packed word.
        for course in report["courses"]:
            placed = course["effective_surface"]
            self.assertTrue(placed["comparable"], course["stream_index"])
            self.assertEqual(placed["total_world_cells"], 262144)
            self.assertLessEqual(len(placed["first_12_changed_cells"]), 12)
            self.assertLessEqual(placed["changed_world_cells"], 262144)
            self.assertLessEqual(
                placed["changed_c000_selectors"], placed["changed_world_cells"]
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
