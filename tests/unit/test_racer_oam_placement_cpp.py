import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class RacerOamPlacementCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "racer-oam-placement-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "presentation"),
                    str(ROOT / "native" / "presentation" / "racer_oam_placement.cpp"),
                    str(ROOT / "tests" / "native" / "racer_oam_placement_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)

    def test_reference_is_explicitly_dynamic_not_fixed_policy(self):
        ref = json.loads(
            (ROOT / "analysis" / "data" / "racer-oam-placement-reference.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(ref["obsel"], "0x83")
        self.assertEqual(ref["slots"]["p1"]["slot"], 98)
        self.assertEqual(ref["slots"]["p1"]["x_raw_9bit"], 104)
        self.assertEqual(ref["slots"]["p1"]["y_raw_8bit"], 40)
        self.assertEqual(ref["slots"]["p1"]["size_pixels"], [64, 64])
        self.assertTrue(ref["slots"]["p1"]["hflip"])
        self.assertFalse(ref["slots"]["p1"]["vflip"])
        self.assertIn("not a fixed runtime position", ref["interpretation"])


if __name__ == "__main__":
    unittest.main()
