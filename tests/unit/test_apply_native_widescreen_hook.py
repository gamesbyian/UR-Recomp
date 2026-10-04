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
            + "    switch (((cpu->m_flag & 1) << 1) | (cpu->x_flag & 1)) {\n"
            + "      case 0: { RecompReturn _r = bank_01_A59E_M0X0(cpu); break; }\n"
            + "      default: break;\n"
            + "    }\n"
            + "    switch (((cpu->m_flag & 1) << 1) | (cpu->x_flag & 1)) {\n"
            + "      case 0: goto L_01A59D;\n"
            + "      default: goto L_01A59D;\n"
            + "    }\n"
            + block("01A59D")
            + "    uint16 _v7 = 0x433;\n"
            + "    cpu_write_y_x(cpu, (uint16)(_v7));\n"
            + "    return RECOMP_RETURN_NORMAL;\n}\n"
            "RecompReturn bank_01_A59E_M0X0(CpuState *cpu) { return RECOMP_RETURN_NORMAL; }\n",
            encoding="utf-8",
        )
        return wrapper

    def test_injects_exact_accepted_seams_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            wrapper=self.make_tree(root)
            report=MOD.apply(root)
            self.assertTrue(report["changed"])
            self.assertTrue(report["margin0_control"])
            self.assertTrue(report["margin8_hook"])
            self.assertTrue(report["vs_margin8_supported"])
            self.assertTrue(report["margin16_supported"])
            self.assertTrue(report["margin24_supported"])
            self.assertTrue(report["margin64_supported"])
            self.assertTrue(report["margin72_supported"])
            self.assertEqual(report["first_constraint"],"none-through-plus72")

            w=wrapper.read_text(encoding="utf-8")
            self.assertIn(MOD.MARKER,w)
            self.assertIn("bank_01_A59E_M0X0(cpu)",w)
            self.assertIn("ur_ws_native_second_pass ? 0x453 : 0x433",w)
            self.assertIn("ur_ws_native_after_builder(cpu)",w)
            self.assertIn("ur_ws_native_cleanup_previous_payload(cpu)",w)
            self.assertIn("cpu->ram[0x0ddb] != 0",w)
            self.assertIn("p1_stock_count == 8",w)
            self.assertIn("p2_stock_count == 8",w)
            self.assertIn("0x0433 + (p1_stock_vertical + p1_stock_count) * 2u",w)
            self.assertIn("0x0475 + (p2_stock_vertical + p2_stock_count) * 2u",w)
            self.assertIn("URWS_VS_PREP margin=8 player=1",w)
            self.assertIn("URWS_VS_PREP margin=8 player=2",w)
            self.assertIn("URWS_VS_CLEANUP margin=8",w)
            self.assertIn("ur_ws_native_write16(cpu, 0x050b",w)
            self.assertIn("ur_ws_native_write16(cpu, 0x0531",w)
            self.assertIn("URWS_SHADOW16 provider=course-runtime",w)
            self.assertIn("URWS_SHADOW24 provider=course-runtime",w)
            self.assertIn("ur_ws_native_shadow_from_course",w)
            self.assertIn("#define UR_WS_NATIVE_MAX_HOST_COLUMNS 8u",w)
            self.assertIn("ur_ws_native_shadow_payload[UR_WS_NATIVE_MAX_HOST_COLUMNS][32]",w)
            self.assertIn("margin < 8 || margin > 72 || (margin & 7) != 0",w)
            self.assertIn('getenv("URRECOMP_WS_VIEW")',w)
            self.assertIn('strcmp(view, "authentic-16x9") == 0',w)
            self.assertIn('strcmp(view, "authentic-16x9-candidate") == 0',w)
            self.assertIn("? 48 : 0",w)
            self.assertIn("URWS_SHADOW_EXT provider=course-runtime",w)
            self.assertIn("0x000f + coarse_index * 2u",w)
            self.assertIn("0x800fu + (uint32)record * 32u",w)
            self.assertNotIn("URRECOMP_WS_SHADOW_ORACLE",w)
            self.assertFalse(MOD.apply(root)["changed"])

    def test_fails_closed_without_live_wrapper(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"bank81_v2.c").write_text(
                "#include \"cpu_state.h\"\nRecompReturn x(CpuState *cpu){return RECOMP_RETURN_NORMAL;}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError,"wrapper TU"):
                MOD.apply(root)

if __name__=="__main__":
    unittest.main()
