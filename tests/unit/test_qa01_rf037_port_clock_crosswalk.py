"""Fail-closed synthetic checks for diagnostic RF037 clock projection."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_rf037_port_clock_crosswalk as m


class CrosswalkTests(unittest.TestCase):
    def sample(self):
        source = [
            dict(age="100", port="2", val="00", v="116", h="100"),
            dict(age="200", port="2", val="C0", v="116", h="356"),
            dict(age="200", port="3", val="FF", v="116", h="356"),
            dict(age="210", port="3", val="04", v="116", h="556"),
        ]
        native = [
            dict(master="1000", frame="2", reg="2142", val="00"),
            dict(master="1100", frame="2", reg="2143", val="FF"),
            dict(master="1100", frame="2", reg="2142", val="C0"),
            dict(master="1300", frame="2", reg="2143", val="04"),
        ]
        return source, native

    def test_normalizes_only_equal_age_source_ambiguity(self):
        source, native = self.sample()
        for i, item in enumerate(native):
            item["scope"] = "writer-A" if i < 2 else "writer-B"
        result = m.crosswalk(source, native)
        self.assertEqual(result["matched_canonical_port_value_prefix"], 4)
        self.assertEqual(result["source_equal_age_pairs_reordered"], 1)
        self.assertEqual(result["native_frames"]["2"]["count"], 4)
        self.assertEqual([(x["scope"], x["first_ordinal"], x["last_ordinal"])
                          for x in result["contiguous_native_writer_scope_segments"]],
                         [("writer-A", 0, 1), ("writer-B", 2, 3)])
        self.assertEqual(result["projection_spc_cycles_per_master_clock"],
                         [15664, 328125])
        gaps = result["same_scanline_cpu_writer_gap_census"]
        self.assertEqual(gaps["compared_consecutive_same_scanline_pairs"], 3)
        self.assertEqual(gaps["gap_difference_histogram_master_clocks"]["156"], 1)
        self.assertEqual(gaps["largest_absolute_gap_differences"][0]["ordinal"], 1)
        self.assertFalse(result["qualified_claims"]["clock_fix_justified"])
        self.assertEqual(result["qualified_claims"]["complete_usa_events_admitted"], 0)

    def test_wrong_value_fails_even_with_similar_time(self):
        source, native = self.sample()
        native[2]["val"] = "C1"
        with self.assertRaisesRegex(ValueError, "mismatch at ordinal 2"):
            m.crosswalk(source, native)

    def test_missing_and_truncated_writers_fail_closed(self):
        source, native = self.sample()
        with self.assertRaisesRegex(ValueError, "unbalanced capture"):
            m.crosswalk(source, native[:-1])
        with self.assertRaisesRegex(ValueError, "truncated"):
            m.crosswalk(source, native, [{"frame": "2"}])
        with self.assertRaisesRegex(ValueError, "source port capture truncated"):
            m.crosswalk(source, native, None, [{"bucket": "1"}])

    def test_nonmonotone_native_clock_fails(self):
        source, native = self.sample()
        native[3]["master"] = "1099"
        with self.assertRaisesRegex(ValueError, "not monotone"):
            m.crosswalk(source, native)

    def test_source_spc_age_reversal_fails(self):
        source, native = self.sample()
        source[-1]["age"] = "199"
        with self.assertRaisesRegex(ValueError, "not monotone"):
            m.crosswalk(source, native)

    def test_report_detects_real_original_truncation_sentinel(self):
        from tempfile import TemporaryDirectory
        from zipfile import ZipFile
        with TemporaryDirectory() as root:
            p = Path(root) / "case.zip"
            with ZipFile(p, "w") as z:
                z.writestr(m.ORIGINAL_LOG,
                           "QA01RF037ORIGCPU2 bucket=1 age=100 port=2 val=00\n"
                           "QA01RF037ORIGCPU2_TRUNCATED bucket=1\n")
                z.writestr(m.NATIVE_LOG,
                           "QA01RF037NATIVEUP kind=rtl-apu-enter "
                           "frame=1 master=1000 reg=2142 val=00\n")
            with self.assertRaisesRegex(ValueError, "source port capture truncated"):
                m.report(p)

    def test_empty_capture_fails(self):
        with self.assertRaisesRegex(ValueError, "unbalanced capture"):
            m.crosswalk([], [])


if __name__ == "__main__":
    unittest.main()
