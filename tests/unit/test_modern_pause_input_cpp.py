import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class ModernPauseInputCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-pause-input-test"
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
                    str(ROOT / "native" / "product" / "host_product_state.cpp"),
                    str(ROOT / "native" / "product" / "session_control.cpp"),
                    str(ROOT / "native" / "product" / "session_runtime_adapter.cpp"),
                    str(ROOT / "native" / "product" / "race_restart_anchor.cpp"),
                    str(ROOT / "native" / "product" / "race_restart_lifecycle.cpp"),
                    str(ROOT / "native" / "product" / "modern_session_runtime.cpp"),
                    str(ROOT / "native" / "product" / "modern_session_c_api.cpp"),
                    str(ROOT / "native" / "product" / "modern_pause_menu.cpp"),
                    str(ROOT / "native" / "product" / "modern_pause_input.cpp"),
                    str(ROOT / "tests" / "native" / "modern_pause_input_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
