import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_native_anchor", ROOT/"tools/inspect_native_widescreen_prep_anchor.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class NativeWidescreenPrepAnchorTests(unittest.TestCase):
    def test_finds_mirrored_and_canonical_targets(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"bank81_part00_v2.c").write_text(
                "x\\n"
                "cpu_trace_block(cpu, 0x81A597);\\n"
                "a\\n"
                "cpu_trace_block(cpu, 0x01A59A);\\n"
                "b\\n"
                "cpu_trace_block(cpu, 0x81A59D);\\n"
                "c\\n"
                "cpu_trace_block(cpu, 0x01A59E);\\n"
                "d\\n"
                "uint16 _v1 = 0x433;\\n"
                "cpu_write_y_x(cpu, (uint16)(_v1));\\n"
                "e\\n"
                "cpu_trace_block(cpu, 0x82D2D1);\\n",
                encoding="utf-8",
            )
            report=MOD.inspect(root, radius=1)
            self.assertTrue(report["all_required_found"])
            self.assertEqual(report["target_counts"]["wrapper_call_a59e"],1)
            self.assertEqual(report["target_counts"]["prep_helper_entry"],1)
            self.assertEqual(report["staging_initializer_count"],1)

    def test_missing_target_fails_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"bank01_v2.c").write_text(
                "cpu_trace_block(cpu, 0x01A597);\\n", encoding="utf-8"
            )
            self.assertFalse(MOD.inspect(root)["all_required_found"])

if __name__=="__main__":
    unittest.main()
