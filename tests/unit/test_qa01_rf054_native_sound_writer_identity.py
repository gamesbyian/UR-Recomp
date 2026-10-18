"""RF054 pinned source probe only; AOT ROM pointer mapping is not a true bus read."""
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf054_native_sound_writer_identity as rf054

class RF054SourceContract(unittest.TestCase):
    def common(self):
        return ("#include \"common_rtl.h\"\n" +
                rf054.COMMON_ROM_HEADER + "  return map;\n}\n" +
                rf054.COMMON_APU_HEADER + "  if (filter) return;\n" +
                rf054.COMMON_APU_SLOT + "  authoritative_real_write();\n}\n")
    def cpu(self):
        return ("#include \"cpu_state.h\"\n" +
                rf054.CPU_BYTE_HEADER + "  return cpu_latch_read8(cpu,*RomPtr(addr));\n}\n" +
                rf054.CPU_WORD_HEADER + "  return cpu_latch_read16(cpu,value);\n}\n")
    def test_rtl_only_observes_actual_one_publication_and_rom_mapping(self):
        before=self.common()
        after=rf054.patch_common(before)
        self.assertEqual(after.count("authoritative_real_write();"),1)
        self.assertEqual(after.count("void RtlApuWrite("),1)
        self.assertEqual(after.count("uint8 *RomPtr("),1)
        self.assertIn('ur_rf054_native_observe("writer", adr, val);',after)
        self.assertIn('ur_rf054_native_observe("rom-map", addr, 0);',after)
        self.assertIn('snes_frame_counter != 6124',after)
        self.assertIn("ROM mapping requests MUST NOT be promoted",after)
        self.assertEqual(rf054.patch_common(after),after)
    def test_real_native_cpu_helper_was_never_extra_issued(self):
        before=self.cpu()
        after=rf054.patch_cpu(before)
        self.assertEqual(after.count("return cpu_latch_read8(cpu,*RomPtr(addr));"),1)
        self.assertEqual(after.count("uint8 cpu_read8("),1)
        self.assertEqual(after.count("uint16 cpu_read16("),1)
        self.assertIn('ur_rf054_actual_bus("read8", cpu, bank, addr);',after)
        self.assertIn('ur_rf054_actual_bus("read16", cpu, bank, addr);',after)
        self.assertIn("QA01RF054NATIVEBUS_TRUNCATED",after)
        self.assertEqual(rf054.patch_cpu(after),after)
    def test_unknown_source_anchor_and_partial_probe_rejected(self):
        with self.assertRaisesRegex(ValueError,"unknown pinned native RTL anchor"):
            rf054.patch_common(self.common().replace("uint8 *RomPtr(","uint8 *MapPointer("))
        with self.assertRaisesRegex(ValueError,"unknown pinned native CPU bus"):
            rf054.patch_cpu(self.cpu().replace("uint8 cpu_read8(","uint8 real_read("))
        with self.assertRaisesRegex(ValueError,"partial/tampered"):
            rf054.patch_common(rf054.patch_common(self.common()).replace("QA01RF054NATIVE kind=","QA01RF054BAD kind="))
        with self.assertRaisesRegex(ValueError,"partial/tampered"):
            rf054.patch_cpu(rf054.patch_cpu(self.cpu()).replace("QA01RF054NATIVEBUS kind=","QA01RF054BAD kind="))
if __name__=="__main__":unittest.main()
