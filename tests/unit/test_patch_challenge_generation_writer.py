import pathlib
import tempfile
import unittest
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import patch_challenge_generation_writer as patcher  # noqa: E402


class ChallengeGenerationWriterPatchTests(unittest.TestCase):
    def test_patches_exact_unique_store_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            src = root / "bank_00.c"
            src.write_text(
                '#include "cpu_state.h"\n'
                'void f(CpuState *cpu) {\n'
                '  cpu_write8(cpu, 0x77, (uint16)(0x10d1), _v42);\n'
                '}\n'
            )
            patched = patcher.patch_sources(root)
            self.assertEqual(patched, src)
            text = src.read_text()
            self.assertIn(
                '#include "uniracers_challenge_generation_bridge.h"',
                text)
            self.assertIn(
                "ur_uniracers_challenge_generation_filter(_v42)",
                text)

            # Applying the patch twice does not duplicate the hook/include.
            self.assertEqual(patcher.patch_sources(root), src)
            text2 = src.read_text()
            self.assertEqual(text2.count(
                "uniracers_challenge_generation_bridge.h"), 1)
            self.assertEqual(text2.count(
                "ur_uniracers_challenge_generation_filter("), 1)

    def test_rejects_missing_store(self):
        with tempfile.TemporaryDirectory() as td:
            src = pathlib.Path(td) / "bank.c"
            src.write_text("void f(void) {}\n")
            with self.assertRaisesRegex(ValueError, "found 0"):
                patcher.patch_sources(src)

    def test_rejects_ambiguous_stores(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "a.c").write_text(
                "cpu_write8(cpu, 0x77, (uint16)(0x10d1), _v1);\n")
            (root / "b.c").write_text(
                "cpu_write8(cpu, 0x77, (uint16)(0x10d1), _v2);\n")
            with self.assertRaisesRegex(ValueError, "found 2"):
                patcher.patch_sources(root)

    def test_does_not_patch_similar_wrong_width_or_address(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "a.c").write_text(
                "cpu_write16(cpu, 0x77, (uint16)(0x10d1), _v1);\n"
                "cpu_write8(cpu, 0x77, (uint16)(0x10d2), _v2);\n")
            with self.assertRaisesRegex(ValueError, "found 0"):
                patcher.patch_sources(root)


if __name__ == "__main__":
    unittest.main()
