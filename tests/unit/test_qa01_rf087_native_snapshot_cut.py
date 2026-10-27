"""RF087 pinned dump-call anchor and fail-closed cut receipt tests."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf087_native_snapshot_cut as patcher
import qa01_rf087_native_snapshot_cut_receipt as receipt


def row(f, master=12345, ptr=0xC6B0, counter=0x9F, rc=0):
    return (f"QA01RF087NATIVECUT f={f} rc={rc} "
            f"master_before={master} master_after={master} "
            f"ptr_before={ptr:04X} ptr_after={ptr:04X} "
            f"counter_before={counter:02X} counter_after={counter:02X}")


class SnapshotCutTests(unittest.TestCase):
    def test_real_dump_call_bracketed_without_extra_guest_operations(self):
        source = "static void ScriptDump(void) {\n" + patcher.ANCHOR + "\n}\n"
        out = patcher.patch(source)
        self.assertEqual(out.count(patcher.STAMP), 1)
        self.assertEqual(out.count("snes_state_dump("), 1)
        self.assertLess(out.index("rf087_master_before = g_cpu.master_cycles"),
                        out.index("int rc = snes_state_dump("))
        self.assertLess(out.index("int rc = snes_state_dump("),
                        out.index("QA01RF087NATIVECUT"))
        self.assertIn("g_ram[0x0063]", out)
        with self.assertRaisesRegex(ValueError, "already or partly"):
            patcher.patch(out)
        with self.assertRaisesRegex(ValueError, "missing/ambiguous"):
            patcher.patch(source.replace("snes_state_dump", "changed_dump"))

    def test_actual_cut_rows_and_release_boundary(self):
        raw = ("noise\n" + row(6058) + "\n" +
               row(6059, 12500, 0xC74D, 0x97) + "\n").encode()
        v = receipt.audit(raw)
        self.assertEqual([r["frame"] for r in v["native_cut_rows"]], [6058, 6059])
        self.assertEqual(v["native_cut_rows"][1]["pointer16_at_cut"], 0xC74D)
        self.assertFalse(v["original_native_clock_registration_proven"])
        self.assertEqual(v["release_credit"], 0)

    def test_missing_partial_changing_and_malformed_fail(self):
        good = [row(6058), row(6059, 12500)]
        mutants = [
            good[:1],
            [good[0], good[1].replace("rc=0", "rc=1")],
            [good[0], good[1].replace("master_after=12500", "master_after=12501")],
            [good[0], good[1].replace("ptr_after=C6B0", "ptr_after=C6B1")],
            [good[0], good[1].replace("counter_after=9F", "counter_after=9E")],
            [good[1], good[0]],
            [good[0], good[1].replace("f=6059", "f=6069")],
            [good[0], good[1] + " junk"],
        ]
        for i, rows in enumerate(mutants):
            with self.subTest(i=i), self.assertRaises(ValueError):
                receipt.audit(("\n".join(rows) + "\n").encode())


if __name__ == "__main__":
    unittest.main()
