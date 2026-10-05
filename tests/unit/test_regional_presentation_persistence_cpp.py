import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class RegionalPresentationPersistenceCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "regional-presentation-persistence-test"
            state_path = pathlib.Path(tmp) / "host-state.txt"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "product"),
                    str(ROOT / "native" / "product" / "output_resolution_policy.cpp"),
                    str(ROOT / "native" / "product" / "host_product_state.cpp"),
                    str(ROOT / "native" / "product" / "host_product_store.cpp"),
                    str(ROOT / "native" / "product" / "regional_presentation_secret.cpp"),
                    str(ROOT / "native" / "product" / "regional_presentation_runtime.cpp"),
                    str(ROOT / "tests" / "native" / "regional_presentation_persistence_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe), str(state_path)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
