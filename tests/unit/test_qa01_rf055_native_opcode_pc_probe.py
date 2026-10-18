"""RF055 generator site must fail closed and leave all guest IR unchanged."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf055_native_opcode_pc_probe as rf

SOURCE=("a\n        for ii, (di_insn, ir_ops) in enumerate(pairs):\n"
        "            if ii in skip_emit_idx: continue\n"
        "            for _ln in _dynamic_charge_lines(di_insn, '6'):\n"
        "                lines.append(_ln)\n"
        "            for op in ir_ops:\n"
        "                lines.append(emit_op(op, getattr(di_insn, 'addr', None)))\n")

class NativePcSite(unittest.TestCase):
    def test_single_source_exact_insertion_idempotent(self):
        x=rf.patch(SOURCE)
        self.assertEqual(rf.patch(x),x)
        self.assertEqual(x.count(rf.MARK),1)
        self.assertEqual(x.count('            for op in ir_ops:\n'),1)
        self.assertIn("di_insn.opcode != 0xB7",x)
        self.assertIn("di_insn.operand != 0x63",x)
        self.assertIn("cpu->master_cycles",x)
        self.assertIn("QA01RF055NATIVEPC_TRUNCATED",x)
        self.assertNotIn("cpu_read8(",x)
        self.assertNotIn("cpu_read16(",x)
    def test_unknown_or_duplicate_emitter_fails_before_write(self):
        for src in ("empty",SOURCE.replace('for op in ir_ops:', 'for op in other_ops:'),
                    SOURCE+rf.ANCHOR):
            with self.subTest(src=src[:20]):
                with self.assertRaisesRegex(ValueError,'pinned'):
                    rf.patch(src)
    def test_corrupt_previous_stage_refused(self):
        with self.assertRaisesRegex(ValueError,'partial/tampered'):
            rf.patch(SOURCE+rf.MARK)
if __name__=='__main__': unittest.main()
