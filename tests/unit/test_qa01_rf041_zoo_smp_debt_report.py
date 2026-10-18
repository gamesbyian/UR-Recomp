"""RF041 independent source/natively calibrated opcode-debt provenance guards."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf041_zoo_smp_debt_report as m

class DebtWitness(unittest.TestCase):
    def fixture(self):
        src = [
            "QA01RF041ORIGCPU phase=before-sync age=103919449 v=116 h=442 debt=-1 pc=154F op=E4 cycle=2 port=2 value=24",
            "QA01RF037ORIGSPC age=103919450 v=116 h=442 pc=154F port=2 val=23",
            "QA01RF041ORIGF6 age=103919450 v=116 h=442 debt=3 pc=154F opcode=E4 cycle=3 port=2 val=23",
            "QA01RF041ORIGCPU phase=after-sync-before-publish age=103919450 v=116 h=442 debt=3 pc=1551 op=E4 cycle=3 port=2 value=24",
            "QA01RF037ORIGCPU2 bucket=38 age=103919450 v=116 h=442 port=2 val=24",
            "QA01RF041ORIGCPU phase=after-publish age=103919450 v=116 h=442 debt=3 pc=1551 op=E4 cycle=3 port=2 value=24",
            "QA01RF037ORIGSPC age=103919457 v=116 h=600 pc=154F port=2 val=24",
            "QA01RF041ORIGF6 age=103919457 v=116 h=600 debt=-2 pc=154F opcode=E4 cycle=1 port=2 val=24",
        ]
        native = [
            "QA01RF041NATIVE kind=spc-read frame=6091 age=103919427 target=103919427 left=0 pc=154F port=2 val=23 q=2",
            "QA01RF037NATIVEBUS kind=apply frame=6091 age=103919434 target=103919434 pc=154D port=2 val=24 q=1",
            "QA01RF041NATIVE kind=apply frame=6091 age=103919434 target=103919434 left=0 pc=154D port=2 val=24 q=1",
            "QA01RF037NATIVEBUS kind=spc-read frame=6091 age=103919434 target=103919434 pc=154F port=2 val=24 q=0",
            "QA01RF041NATIVE kind=spc-read frame=6091 age=103919434 target=103919434 left=4 pc=154F port=2 val=24 q=0",
        ]
        return "\n".join(src)+"\n", "\n".join(native)+"\n"

    def test_actual_debt_read_before_published_and_native_apply_before_read(self):
        r = m.analyze(*self.fixture())
        self.assertEqual([x["phase"] for x in r["source_cpu_sync_and_publication"]],
                         ["before-sync", "after-sync-before-publish", "after-publish"])
        self.assertEqual([x["debt"] for x in r["source_f6_debt_old_and_new"]],
                         ["3", "-2"])
        self.assertEqual(r["native_queue_apply"]["left"], "0")
        self.assertEqual(r["native_first_new_f6"]["left"], "4")
        self.assertFalse(r["source_qualified_scheduling_fix_proven"])
        self.assertFalse(r["absolute_original_native_spc_clock_phase_equivalent"])
        self.assertEqual(r["accepted_usa_events"], 0)

    def test_missing_original_phase_fails(self):
        a, b = self.fixture()
        with self.assertRaisesRegex(ValueError, "missing/duplicate"):
            m.analyze(a.replace("phase=after-sync-before-publish",
                                "phase=removed"), b)

    def test_wrong_order_fails_even_at_same_recorded_spc_age(self):
        a, b = self.fixture()
        parts = a.splitlines()
        parts[1], parts[4] = parts[4], parts[1]
        with self.assertRaisesRegex(ValueError, "read-old"):
            m.analyze("\n".join(parts)+"\n", b)
        n = b.splitlines()
        n[1], n[3] = n[3], n[1]
        with self.assertRaisesRegex(ValueError, "queue/F6|apply before"):
            m.analyze(a, "\n".join(n)+"\n")

    def test_lost_or_truncated_debt_never_completes(self):
        a, b = self.fixture()
        with self.assertRaisesRegex(ValueError, "missing/duplicate"):
            m.analyze(a.replace("QA01RF041ORIGF6 age=103919457", "missing age=103919457"), b)
        with self.assertRaisesRegex(ValueError, "truncated"):
            m.analyze(a, b+"QA01RF041NATIVE_TRUNCATED frame=6091\n")

if __name__ == "__main__":
    unittest.main()
