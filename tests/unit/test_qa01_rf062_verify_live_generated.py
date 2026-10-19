"""RF062: actual live M1X0 generated body required before authentic replay."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf062_verify_live_generated as rf


class LiveModeSource(unittest.TestCase):
    @staticmethod
    def generated(mode="M1X0", *, shim=True):
        call = ("uint8 v42 = ur_rf062_read8_pc_8282f0(cpu, 0x11, "
                "((uint16)cpu->Y)); /* UR_QA01_RF062_DIRECT_PC_8282F0 */") if shim else (
                    "uint8 v42 = cpu_read8_paced(cpu, 0x11, ((uint16)cpu->Y));")
        return (
            "RecompReturn Snd_UploadBlockList_82EF_%s(CpuState *cpu) {\n" % mode
            + "  label_82EF:\n"
            + "  " + call + "\n"
            + "  return RECOMP_RETURN_NORMAL;\n"
            + "}\n"
            + "RecompReturn OtherFunction(CpuState *cpu) {\n"
            + "  return RECOMP_RETURN_NORMAL;\n"
            + "}\n"
        )

    def test_real_live_mode_required_not_decoy_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "live.c").write_text(self.generated())
            r = rf.audit(root)
            self.assertEqual(r["source_provenance"]["direct_original_8282F0_real_bus_read_callsites"], 1)
            self.assertFalse(r["actual_native_ROM_bus_read_pc_proven"])
            self.assertEqual(r["accepted_complete_USA_events"], 0)

    def test_nonexecuted_m0x0_decoy_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "wrong.c").write_text(self.generated(mode="M0X0"))
            with self.assertRaisesRegex(ValueError, "missing/duplicated live"):
                rf.audit(root)
            (root / "right.c").write_text(self.generated(mode="M1X0", shim=False))
            with self.assertRaisesRegex(ValueError, "lacks real executed"):
                rf.audit(root)
            (root / "right.c").write_text(self.generated())
            with self.assertRaisesRegex(ValueError, "missing/duplicated live"):
                (root / "other.c").write_text(self.generated())
                rf.audit(root)

    def test_function_scope_not_other_compiled_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = self.generated(mode="M1X0", shim=False)
            text += "RecompReturn Decoy(CpuState *cpu) {\n"
            text += "  uint8 x = ur_rf062_read8_pc_8282f0(cpu, 0x11, cpu->Y); /* UR_QA01_RF062_DIRECT_PC_8282F0 */\n}\n"
            (root / "src.c").write_text(text)
            with self.assertRaisesRegex(ValueError, "lacks real executed"):
                rf.audit(root)


if __name__ == "__main__":
    unittest.main()
