import pathlib
import tempfile
import unittest

from tools.extract_generated_challenge_qualification import analyze


class GeneratedChallengeQualificationTests(unittest.TestCase):
    def test_extracts_named_variant_and_references(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "bank03.c").write_text(
                "RecompReturn TourStuntQualificationThreshold_M0X0(CpuState *cpu) {\n"
                "  uint16 _v1 = cpu_read16(cpu, 0x77, (uint16)(0x069c + cpu->X));\n"
                "  uint16 _v2 = cpu_read16(cpu, 0x83, (uint16)(0xa218 + cpu->X));\n"
                "  if (_v1) { _v2++; }\n"
                "  return RECOMP_RETURN_NORMAL;\n"
                "}\n",
                encoding="utf-8",
            )
            report = analyze(root)
            self.assertEqual(len(report["variants"]), 1)
            self.assertTrue(report["all_variants_reference_medal_offset"])
            self.assertTrue(report["all_variants_reference_threshold_table"])

    def test_rejects_missing_routine(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "bank.c").write_text("void f(void) {}\n")
            with self.assertRaisesRegex(ValueError, "no generated"):
                analyze(root)


if __name__ == "__main__":
    unittest.main()
