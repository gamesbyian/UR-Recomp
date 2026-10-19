"""RF076 generated C gate negative and positive tests; no ROM required."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf076_generated_exec_pc_gate as gate


class GeneratedGate(unittest.TestCase):
    def test_emitted_targets_pass_without_claiming_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generated = root / "different/output/guest_aot.c"
            generated.parent.mkdir(parents=True)
            generated.write_text("\n".join(
                f"ur_rf047_mark_executed_pc(0x{pc:06X}u, 1u);"
                for pc in sorted(gate.REQUIRED)))
            result = gate.inspect(root)
            self.assertTrue(result["static_generated_calls_present"])
            self.assertFalse(result["actual_guest_opcode_executed"])
            self.assertEqual(result["accepted_USA_events"], 0)
            self.assertEqual(result["generated_translation_units"][0]["path"],
                             "different/output/guest_aot.c")

    def test_runtime_recorder_cannot_substitute_for_generated_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recorder = root / "snesrecomp/runner/src/beam_frame_driver.c"
            recorder.parent.mkdir(parents=True)
            recorder.write_text("\n".join(
                f"ur_rf047_mark_executed_pc(0x{pc:06X}u, 1u);"
                for pc in gate.REQUIRED))
            with self.assertRaisesRegex(ValueError, "no generated C"):
                gate.inspect(root)

    def test_missing_target_is_hard_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "aot.c").write_text("\n".join(
                f"ur_rf047_mark_executed_pc(0x{pc:06X}u, 1u);"
                for pc in sorted(gate.REQUIRED)[:-1]))
            with self.assertRaisesRegex(ValueError, "missing generated opcode-PC targets"):
                gate.inspect(root)

    def test_declaration_only_is_hard_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "aot.c").write_text(
                "extern void ur_rf047_mark_executed_pc(uint32_t, unsigned);")
            with self.assertRaisesRegex(ValueError, "no generated C"):
                gate.inspect(root)


if __name__ == "__main__":
    unittest.main()
