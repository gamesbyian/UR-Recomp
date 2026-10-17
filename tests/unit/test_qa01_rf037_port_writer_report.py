"""RF037 original/native writer report must keep original SPC-age and native host axes distinct."""
import io
import json
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_rf037_port_writer_report as m


class SourceWriterReportTests(unittest.TestCase):
    def case(self):
        out = io.BytesIO()
        with ZipFile(out, "w") as z:
            z.writestr(m.ORIGINAL_LOG, "\n".join([
                "QA01RF037ORIGCPU2 bucket=1 age=103322523 v=1 h=2 port=2 val=00",
                "QA01RF037ORIGCPU2 bucket=1 age=103322541 v=1 h=3 port=3 val=04",
                "QA01RF037ORIGOP_TRUNCATED frame=6073",
                "junk text",
            ]) + "\n")
            z.writestr(m.NATIVE_LOG, "\n".join([
                "QA01RF037NATIVECPU kind=byte frame=6056 master=100 bank=80 reg=2142 val=00 scope=foo",
                "QA01RF037NATIVEUP kind=write-reg frame=6056 master=100 reg=2142 val=00 scope=foo",
                "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6056 master=100 reg=2142 val=00 scope=foo",
                "QA01RF037NATIVEUP kind=rtl-apu-after-filter frame=6056 master=100 reg=2142 val=00 scope=foo",
                "QA01RF037NATIVEBUS kind=schedule frame=6056 age=103322463 target=103322524 pc=FFCF port=2 val=00 q=1",
                "QA01RF037NATIVEBUS kind=schedule frame=6056 age=103322463 target=103322541 pc=FFCF port=3 val=04 q=1",
                "QA01RF037NATIVECPU_TRUNCATED frame=6057",
            ]) + "\n")
            z.writestr("case-result.json", json.dumps({
                "case": "zoom-zoo",
                "disposition": "strict_candidate",
                "evidence": {
                    "original_event_frames": 5163,
                    "next_bowl_bounded": {
                        "fresh_native_entry_offset": 267,
                        "fresh_original_entry_offset": 267,
                        "all_sampled_sram_pairs_equal": True,
                    },
                },
            }))
        out.seek(0)
        return ZipFile(out)

    def test_numeric_ages_and_writer_stages_separately(self):
        with self.case() as z:
            v = m.report(z)
        self.assertEqual(v["original"]["port_writes"], 2)
        self.assertEqual(v["original"]["age_first_last"], [103322523, 103322541])
        self.assertEqual(v["original"]["opcode_truncated_frames"], [6073])
        self.assertEqual(v["native"]["cpu_writer_count"], 1)
        self.assertEqual(v["native"]["upstream_stage_counts"],
                         {"write-reg": 1, "rtl-apu-enter": 1, "rtl-apu-after-filter": 1})
        self.assertEqual(v["native"]["writer_truncation"][0]["frame"], "6057")
        self.assertEqual(v["native"]["native_by_frame"]["6056"]["write-reg"], 1)
        candidates = v["native"]["schedule_nearest_source_value"]
        self.assertEqual([x["native_minus_nearest_original_spc_cycles"]
                          for x in candidates], [1, 0])
        self.assertTrue(all(not x["is_time_aligned_proof"] for x in candidates))
        self.assertEqual(v["bounded_control"]["release_credit"], 0)

    def test_unknown_log_lines_and_no_matching_age(self):
        self.assertIsNone(m.event("QA01RF037NATIVEPTR frame=6057 val=0034"))
        self.assertIsNone(m.event("ordinary log line"))
        self.assertEqual(m.event("QA01RF037NATIVEUP kind=write-reg frame=6055"),
                         ("QA01RF037NATIVEUP", {"kind": "write-reg", "frame": "6055"}))

    def test_source_scope_persists_as_research_only(self):
        self.assertIn("SPC-age", m.__doc__)
        self.assertNotIn("release_credit\": 1", (ROOT/"tools/qa01_rf037_port_writer_report.py").read_text())


if __name__ == "__main__":
    unittest.main()
