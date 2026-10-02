import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_hook", ROOT/"tools/apply_native_widescreen_hook.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

def block(pc: str) -> str:
    return f"""L_{pc}:
    cpu_trace_block(cpu, 0x{pc});
    WatchdogCheck();
    if (interp_bridge_lle_master_deadline_reached(cpu)) {{
      return RECOMP_RETURN_NORMAL;
    }}
    cpu->coprocessor_master_cycles = cpu->master_cycles;
"""

class NativeWidescreenHookTests(unittest.TestCase):
    def make_tree(self, root: Path):
        wrapper = root/"bank01_v2.c"
        wrapper.write_text(
            "#include \"cpu_state.h\"\n"
            "RecompReturn proto(CpuState *cpu);\n"
            "RecompReturn WidescreenPrepareWrapper_M0X0(CpuState *cpu) {\n"
            + block("01A59A")
            + "      RecompReturn _r = bank_01_A59E_M0X0(cpu);\n"
            + block("01A59D")
            + block("01A5A3")
            + "    return RECOMP_RETURN_NORMAL;\n}\n"
            "RecompReturn bank_01_A59E_M0X0(CpuState *cpu) { return RECOMP_RETURN_NORMAL; }\n",
            encoding="utf-8",
        )
        nmi = root/"bank02_v2.c"
        nmi.write_text(
            "#include \"cpu_state.h\"\n"
            "RecompReturn I_NMI(CpuState *cpu) {\n"
            + block("02D2D1")
            + "    return RECOMP_RETURN_NORMAL;\n}\n",
            encoding="utf-8",
        )
        return wrapper,nmi

    def test_injects_exact_accepted_seams_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            wrapper,nmi=self.make_tree(root)
            report=MOD.apply(root)
            self.assertTrue(report["changed"])
            self.assertTrue(report["margin0_control"])
            self.assertTrue(report["margin8_hook"])
            self.assertFalse(report["margin16_supported"])
            self.assertEqual(report["first_constraint"],"secondary-lane-capacity")

            w=wrapper.read_text(encoding="utf-8")
            n=nmi.read_text(encoding="utf-8")
            self.assertIn(MOD.MARKER,w)
            self.assertIn("bank_01_A59E_M0X0(cpu)",w)
            self.assertIn("cpu->Y = 0x0453",w)
            self.assertIn("ur_ws_native_after_builder(cpu)",w)
            self.assertIn("ur_ws_native_cleanup_after_nmi(cpu)",n)
            self.assertFalse(MOD.apply(root)["changed"])

    def test_fails_closed_without_nmi_cleanup_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.make_tree(root)
            (root/"bank02_v2.c").write_text(
                "#include \"cpu_state.h\"\nRecompReturn x(CpuState *cpu){return RECOMP_RETURN_NORMAL;}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError,"NMI cleanup TU"):
                MOD.apply(root)

if __name__=="__main__":
    unittest.main()
