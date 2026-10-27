"""Synthetic RF086 actual-WRAM-commit guards, not native Zoo admission."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf086_native_first_boundary_commit as patcher
import qa01_rf086_native_first_boundary_receipt as receipt


def fixture():
    # The pinned framework's actual WRAM-store anchors, NOT invented bank82
    # non-FastRom generated functions. The latter do not exist upstream.
    return (
        '#include "cpu_state.h"\n'
        'void cpu_write8(CpuState *cpu, uint8 bank, uint16 addr, uint8 v) {\n'
        '    int off = cpu_wram_offset(bank, addr);\n'
        '    if (off >= 0) {\n'
        '        uint8 old = cpu->ram[off];\n'
        '        cpu->ram[off] = v;\n'
        '        /* Optional title hook for game-specific stage-window tracking. */\n'
        '        return;\n    }\n}\n'
        'void cpu_write16(CpuState *cpu, uint8 bank, uint16 addr, uint16 v) {\n'
        '    int off = cpu_wram_offset(bank, addr);\n'
        '    if (off >= 0 && off + 1 < 0x20000) {\n'
        '        uint16 old = (uint16)cpu->ram[off];\n'
        '        cpu->ram[off]     = (uint8)(v & 0xFF);\n'
        '        cpu->ram[off + 1] = (uint8)(v >> 8);\n'
        '        cpu->open_bus = (uint8)(v >> 8);\n'
        '        return;\n    }\n}\n'
    )


def row(seq, scope, frame=6058, master=1000, after_override=None):
    width, offset = receipt.SITES[scope]
    old, supplied = (0xB0, 0xB1) if width == 2 else (0x9F, 0)
    after = supplied if after_override is None else after_override
    return (
        f"QA01RF086NATIVE seq={seq} scope={scope} f={frame} width={width} "
        f"D=0000 addr={offset:04X} old={old:04X} supplied={supplied:04X} "
        f"rawAfter={after:04X} native_master={master}")


class FirstBoundaryBusCommitTests(unittest.TestCase):
    def test_real_wram_postcommit_hooks_and_no_extra_guest_bus(self):
        before = fixture()
        after = patcher.patch(before)
        self.assertEqual(after.count(patcher.STAMP), 1)
        self.assertEqual(after.count("ur_rf086_after(cpu,"), 2)
        for call in ("cpu_read8_paced(", "cpu_read16_paced(",
                     "cpu_write8_paced(", "cpu_write16_paced("):
            self.assertEqual(before.count(call), after.count(call))
        self.assertLess(after.index("cpu->ram[off] = v;"),
                        after.index("ur_rf086_after(cpu, 1u"))
        self.assertLess(after.index("cpu->ram[off + 1] = (uint8)(v >> 8);"),
                        after.index("ur_rf086_after(cpu, 2u"))
        self.assertIn("cpu->master_cycles", after)
        self.assertIn("QA01RF086NATIVE_TRUNCATED", after)
        self.assertIn("flag[1] != '\\0'", after)
        self.assertIn("g_last_recomp_func", after)
        self.assertNotIn("RecompReturn Snd_IncDataPtr_M0X0", after)

    def test_source_drift_and_reapplication_refused(self):
        source = fixture()
        with self.assertRaisesRegex(ValueError, "already or partly"):
            patcher.patch(patcher.patch(source))
        for anchor in (patcher.ENTRY, patcher.BYTE, patcher.WORD):
            with self.subTest(anchor=anchor[:40]), self.assertRaisesRegex(
                    ValueError, "missing/ambiguous"):
                patcher.patch(source.replace(anchor, "DRIFT", 1))

    def test_actual_submodule_if_checked_out(self):
        path = Path(__file__).resolve().parents[2] / "baldosa" / patcher.FILE
        if path.exists():
            after = patcher.patch(path.read_text(encoding="utf-8"))
            self.assertEqual(after.count(patcher.STAMP), 1)

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
            [good[0], good[1].replace("native_master=1001",
                                     "native_master=999"), good[2]],
            [good[0].replace("scope=Snd_IncDataPtr_M0X0",
                             "scope=unknown")] + good[1:],
        ]
        for i, rows in enumerate(mutations):
            with self.subTest(i=i), self.assertRaises(ValueError):
                receipt.audit(("\n".join(rows) + "\n").encode())

    def test_workflow_stages_and_retains_bounded_receipt(self):
        workflow = (Path(__file__).resolve().parents[2] /
                    ".github/workflows/qa01-event-campaign.yml").read_text()
        self.assertLess(workflow.index(
            "tools/qa01_rf084_native_sound_dp_committed_writer.py --root baldosa"),
            workflow.index(
            "tools/qa01_rf086_native_first_boundary_commit.py --root baldosa"))
        self.assertLess(workflow.index(
            "tools/qa01_rf086_native_first_boundary_commit.py --root baldosa"),
            workflow.index("cmake -S baldosa -B baldosa/build"))
        self.assertIn("tools/qa01_rf086_native_first_boundary_receipt.py",
                      workflow)
        self.assertIn("qa01-rf086-native-first-boundary.json", workflow)


if __name__ == "__main__":
    unittest.main()
