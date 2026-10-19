"""Reject any non-RF062 source/guest generator changes in comparison."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf062_wrapper_only_diff as diff

OLD = ("RecompReturn Snd_UploadBlockList_82EF_M1X0(CpuState *cpu) {\n"
       "  v1 = cpu_read8_paced(cpu, b, a);\n"
       "}\nRecompReturn next_scene(CpuState *cpu) { return DONE; }\n")
NEW = OLD.replace("cpu_read8_paced(cpu, b, a);",
                  "ur_rf062_read8_pc_8282f0(cpu, b, a); /* UR_QA01_RF062_DIRECT_PC_8282F0 */")

class RF062CodeSwap(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        root=Path(t.name)
        self.a,self.b=root/"control",root/"wrapped"
        self.a.mkdir()
        self.b.mkdir()
        for base,source in ((self.a,OLD),(self.b,NEW)):
            (base/"sound.c").write_text(source)
            (base/"other.c").write_text("RecompReturn noop(void) {return DONE;}\n")
            (base/"runtime.h").write_text("#pragma once\n")

    def test_positive_exact_one_native_paced_read_swap(self):
        result=diff.check(self.a,self.b)
        self.assertTrue(result["only_one_live_generated_c_file_changed"])
        self.assertEqual(result["changed_generated_file"],"sound.c")
        self.assertFalse(result["source_guest_rom_execution_or_noninterference_proven"])
        self.assertEqual(result["accepted_USA_events"],0)

    def test_second_generated_file_changed_must_fail(self):
        (self.b/"other.c").write_text("WRONG")
        with self.assertRaisesRegex(ValueError,"exactly one generated"):
            diff.check(self.a,self.b)

    def test_unapproved_retimming_or_guest_register_change_fails(self):
        (self.b/"sound.c").write_text(NEW.replace("return DONE;", "return PAUSE;"))
        with self.assertRaisesRegex(ValueError,"beyond one original paced read"):
            diff.check(self.a,self.b)

    def test_repeated_or_unwrapped_site_fails(self):
        (self.b/"sound.c").write_text(OLD)
        with self.assertRaisesRegex(ValueError,"exactly one generated"):
            diff.check(self.a,self.b)
        (self.b/"sound.c").write_text(NEW.replace(
            "ur_rf062_read8_pc_8282f0(cpu, b, a)",
            "ur_rf062_read8_pc_8282f0(cpu, b, a) + ur_rf062_read8_pc_8282f0(cpu, b, a)"))
        with self.assertRaisesRegex(ValueError,"beyond one original paced read"):
            diff.check(self.a,self.b)

    def test_only_wrong_variant_instrumented_fails(self):
        (self.b/"sound.c").write_text(
            OLD.replace("next_scene", "other_fn").replace(
                "return DONE;", "return ur_rf062_read8_pc_8282f0(cpu,b,a); /* UR_QA01_RF062_DIRECT_PC_8282F0 */", 1))
        with self.assertRaises(ValueError):
            diff.check(self.a,self.b)


if __name__=="__main__":
    unittest.main()
