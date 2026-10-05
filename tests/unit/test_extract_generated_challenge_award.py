import pathlib
import tempfile
import unittest

from tools.extract_generated_challenge_award import analyze


class GeneratedChallengeAwardTests(unittest.TestCase):
    def test_extracts_named_award_variant(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "bank03.c").write_text(
                "RecompReturn TourResultQualificationAndAward_M1X1(CpuState *cpu) {\n"
                "  uint8 _v1 = cpu_read8(cpu, 0x77, (uint16)(0x069c + cpu->X));\n"
                "  cpu_write8(cpu, 0x77, (uint16)(0x069c + cpu->X), _v1);\n"
                "  return RECOMP_RETURN_NORMAL;\n"
                "}\n",
                encoding="utf-8",
            )
            report = analyze(root)
            self.assertEqual(len(report["variants"]), 1)
            self.assertTrue(report["all_variants_reference_medal_cell"])

    def test_rejects_missing_routine(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "bank.c").write_text("void f(void) {}\n")
            with self.assertRaisesRegex(ValueError, "no generated"):
                analyze(root)


if __name__ == "__main__":
    unittest.main()
