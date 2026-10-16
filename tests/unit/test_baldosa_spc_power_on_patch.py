import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_spc_power_on_patch as fix  # noqa: E402

# Verbatim baldosa/snesrecomp@075fbe4 runner/src/snes/apu.c apu_reset().
PINNED = 'void apu_reset(Apu* apu) {\n  apu->romReadable = true; // before resetting spc, because it reads reset vector from it\n  spc_reset(apu->spc);\n  dsp_reset(apu->dsp);\n  memset(apu->ram, 0, sizeof(apu->ram));\n  apu->dspAdr = 0;\n  apu->cycles = 0;\n  memset(apu->inPorts, 0, sizeof(apu->inPorts));\n  memset(apu->outPorts, 0, sizeof(apu->outPorts));\n  for(int i = 0; i < 3; i++) {\n    apu->timer[i].cycles = 0;\n    apu->timer[i].divider = 0;\n    apu->timer[i].target = 0;\n    apu->timer[i].counter = 0;\n    apu->timer[i].enabled = false;\n  }\n  apu->cpuCyclesLeft = 7;\n  apu->portClock = 0;\n  apu_clearPortQueue(apu);\n}\n'


class PatchTest(unittest.TestCase):
    def test_anchors_guest_time_at_reset_once(self):
        out = fix.patch(PINNED)
        self.assertIn("apu->portTimeValid = true;", out)
        self.assertLess(out.index("apu_clearPortQueue(apu);"), out.index("apu->portTimeValid = true;"))
        self.assertEqual(fix.patch(out), out)

    def test_rejects_unknown_revision_and_tampering(self):
        with self.assertRaisesRegex(ValueError, "not recognized"):
            fix.patch(PINNED.replace("apu->cpuCyclesLeft = 7;", "apu->cpuCyclesLeft = 8;"))
        with self.assertRaisesRegex(ValueError, "altered"):
            fix.patch(fix.patch(PINNED).replace("portTimeValid = true", "portTimeValid = false"))


if __name__ == "__main__":
    unittest.main()
