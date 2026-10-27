"""Synthetic RF086 generated-code and receipt guards, not native Zoo admission."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf086_native_first_boundary_commit as patcher
import qa01_rf086_native_first_boundary_receipt as receipt


def fixture():
    source = patcher.HEADER + "/* UR_QA01_RF084_NATIVE_SOUND_DP_COMMIT */\n"
    for name, width, offset in patcher.SITES:
        source += (
            f"RecompReturn {name}(CpuState *cpu) {{\n"
            f"  L_8151_M1X0:\n  {{\n    uint16 _im = 42;\n"
            f"    cpu_write{width * 8}_paced(cpu, 0x00, "
            f"(uint16)(cpu->D + 0x{offset:04X}), _im);\n"
            f"  }}\n}}\n")
    return source + "RecompReturn NextFunc(CpuState *cpu) {\n}\n"


def row(seq, scope, frame=6058, master=1000, after_override=None):
    width, offset = receipt.SITES[scope]
    old, supplied = (0xB0, 0xB1) if width == 2 else (0x9F, 0)
    after = supplied if after_override is None else after_override
    return (
        f"QA01RF086NATIVE seq={seq} scope={scope} f={frame} width={width} "
        f"D=0000 addr={offset:04X} old={old:04X} supplied={supplied:04X} "
        f"rawAfter={after:04X} native_master={master}")


class FirstBoundaryNonFastTests(unittest.TestCase):
    def test_exact_postcommit_and_no_new_bus_helpers(self):
        before = fixture()
        after = patcher.patch(before)
        self.assertEqual(after.count(patcher.STAMP), 1)
        self.assertEqual(after.count('ur_rf086_after(cpu, "'), 3)
        for call in ("cpu_read8_paced(", "cpu_read16_paced(",
                     "cpu_write8_paced(", "cpu_write16_paced("):
            self.assertEqual(before.count(call), after.count(call))
        for name, width, offset in patcher.SITES:
            start = after.index(f"RecompReturn {name}")
            end = after.index("\nRecompReturn ", start)
            body = after[start:end]
            self.assertLess(body.index(f"cpu_write{width * 8}_paced("),
                            body.index(f'ur_rf086_after(cpu, "{name}"'))
            self.assertIn(f"cpu->ram[ur_rf086_addr_{offset:04x}]", body)
        self.assertIn("cpu->master_cycles", after)
        self.assertIn("QA01RF086NATIVE_TRUNCATED", after)
        self.assertIn("flag[1] != '\\0'", after)

    def test_source_drift_and_reapplication_refused(self):
        source = fixture()
        with self.assertRaisesRegex(ValueError, "already or partly"):
            patcher.patch(patcher.patch(source))
        with self.assertRaisesRegex(ValueError, "missing/ambiguous"):
            patcher.patch(source.replace("Snd_IncDataPtr_M1X0", "WrongFunc"))
        with self.assertRaisesRegex(ValueError, "missing/ambiguous real paced"):
            patcher.patch(source.replace("cpu_write8_paced", "cpu_write8"))
        with self.assertRaisesRegex(ValueError, "must follow RF084"):
            patcher.patch(source.replace("UR_QA01_RF084_NATIVE_SOUND_DP_COMMIT", "old"))

    def test_native_postwrite_receipt_and_mismatch_are_distinct(self):
        names = list(receipt.SITES)
        lines = [row(i + 1, name, master=1000 + i)
                 for i, name in enumerate(names)]
        result = receipt.audit(("noise\n" + "\n".join(lines) + "\n").encode())
        self.assertEqual(result["native_postcommit_rows"], 3)
        self.assertEqual(result["raw_after_mismatch_count"], 0)
        self.assertFalse(result["original_native_clock_registration_proven"])
        self.assertEqual(result["release_credit"], 0)
        lines[0] = row(1, names[0], after_override=0xB2)
        self.assertEqual(receipt.audit(("\n".join(lines) + "\n").encode())
                         ["raw_after_mismatch_count"], 1)

    def test_missing_truncated_malformed_and_reordered_fail(self):
        names = list(receipt.SITES)
        good = [row(i + 1, name, master=1000 + i)
                for i, name in enumerate(names)]
        mutations = [
            good[:2],
            good + ["QA01RF086NATIVE_TRUNCATED"],
            [good[0].replace("seq=1", "seq=2")] + good[1:],
            [good[0].replace("addr=0063", "addr=0064")] + good[1:],
            [good[0].replace("f=6058", "f=6062")] + good[1:],
            [good[0], good[1].replace("native_master=1001", "native_master=999"), good[2]],
            [good[0].replace("scope=Snd_IncDataPtr_M0X0", "scope=unknown")] + good[1:],
        ]
        for i, rows in enumerate(mutations):
            with self.subTest(i=i), self.assertRaises(ValueError):
                receipt.audit(("\n".join(rows) + "\n").encode())

    def test_workflow_stages_and_retains_bounded_receipt(self):
        workflow = (Path(__file__).resolve().parents[2] /
                    ".github/workflows/qa01-event-campaign.yml").read_text()
        self.assertLess(workflow.index(
            "tools/qa01_rf084_native_sound_dp_committed_writer.py --root baldosa"),
            workflow.index("tools/qa01_rf086_native_first_boundary_commit.py --root baldosa"))
        self.assertLess(workflow.index(
            "tools/qa01_rf086_native_first_boundary_commit.py --root baldosa"),
            workflow.index("cmake -S baldosa -B baldosa/build"))
        self.assertIn("tools/qa01_rf086_native_first_boundary_receipt.py", workflow)
        self.assertIn("qa01-rf086-native-first-boundary.json", workflow)


if __name__ == "__main__":
    unittest.main()
