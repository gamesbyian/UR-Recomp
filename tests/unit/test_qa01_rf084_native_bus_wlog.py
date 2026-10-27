"""Synthetic RF084 bus-writer transport tests; no original/native admission."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as qa


class NativeBusWlogTransportTests(unittest.TestCase):
    def test_exact_opt_in_only_for_actual_zoo_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            env = {"UR_QA01_RF084_NATIVE_SOUND_DP": "1",
                   "SNESRECOMP_WLOG_ADDR": "old",
                   "SNESRECOMP_WLOG_STATE": "1",
                   "SNESRECOMP_WLOG_ADDR_HALT": "0063:01"}
            path = qa.configure_rf084_native_bus_wlog(
                env, out, case="zoom-zoo", script_name="complete.script")
            self.assertEqual(path, out / qa.RF084_BUS_WLOG_NAME)
            self.assertEqual(env["SNESRECOMP_WLOG_ADDR"], f"0062:0069:{path}")
            self.assertEqual(env["SNESRECOMP_WLOG_ADDR_CAP"],
                             str(qa.RF084_BUS_WLOG_CAP))
            self.assertNotIn("SNESRECOMP_WLOG_STATE", env)
            self.assertNotIn("SNESRECOMP_WLOG_ADDR_HALT", env)
            self.assertEqual(env["UR_QA01_RF084_NATIVE_SOUND_DP"], "1")

    def test_calibration_other_cases_and_disabled_do_not_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            for flag, case, script in (
                ("1", "zoom-zoo", "entry.script"),
                ("1", "bowl", "complete.script"),
                ("0", "zoom-zoo", "complete.script"),
                ("true", "zoom-zoo", "complete.script"),
            ):
                with self.subTest(flag=flag, case=case, script=script):
                    env = {"UR_QA01_RF084_NATIVE_SOUND_DP": flag,
                           "SNESRECOMP_WLOG_ADDR": "inherited",
                           "SNESRECOMP_WLOG_ADDR_CAP": "999",
                           "SNESRECOMP_WLOG_STATE": "1",
                           "SNESRECOMP_WLOG_ADDR_HALT": "0063:01"}
                    self.assertIsNone(qa.configure_rf084_native_bus_wlog(
                        env, Path(tmp), case=case, script_name=script))
                    self.assertFalse(any(k.startswith("SNESRECOMP_WLOG_")
                                         for k in env))

    def test_nonempty_uncapped_bus_log_is_evidence_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / qa.RF084_BUS_WLOG_NAME
            p.write_text("f6058 00:0063=004D w2 fn\n"
                         "f6059 00:0069=97 w1 fn\n", encoding="utf-8")
            self.assertEqual(qa.verify_rf084_native_bus_wlog(p, cap=3), 2)

    def test_missing_empty_and_capped_logs_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / qa.RF084_BUS_WLOG_NAME
            with self.assertRaises(qa.CompleteEventError):
                qa.verify_rf084_native_bus_wlog(p, cap=3)
            p.touch()
            with self.assertRaises(qa.CompleteEventError):
                qa.verify_rf084_native_bus_wlog(p, cap=3)
            p.write_text("a\nb\nc\n", encoding="utf-8")
            with self.assertRaises(qa.CompleteEventError):
                qa.verify_rf084_native_bus_wlog(p, cap=3)


    def test_case_artifact_retains_native_bus_writer_evidence(self):
        # A successful producer is not useful if its only causal bus log is
        # deleted with the hosted runner. Keep it in the existing case ZIP.
        workflow = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text()
        artifact = workflow.split(
            "      - name: Always retain per-case receipt and bounded diagnostic logs",
            1)[1].split("\n  aggregate:", 1)[0]
        expected = ("${{ runner.temp }}/qa01-case/work/"
                    "${{ matrix.case }}/replay/native/" + qa.RF084_BUS_WLOG_NAME)
        self.assertIn("if: always()", artifact)
        self.assertEqual(artifact.count(expected), 1)


if __name__ == "__main__":
    unittest.main()
