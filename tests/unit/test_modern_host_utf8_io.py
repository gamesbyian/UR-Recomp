"""ROM-free Unicode path checks for the native Modern host's file boundaries."""
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class ModernHostUtf8IoTests(unittest.TestCase):
    def test_real_host_uses_native_paths_at_io_boundaries(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('#include "local_tournament_utf8_path.hpp"', source)
        for value in (
            "g_onboarding_seen_path",
            "g_product_state_path",
            "input_path",
            'stored_path + ".input"',
            "root.save_root",
        ):
            self.assertIn(f"host_native_path_from_utf8({value})", source)
        for raw in (
            "std::ifstream in(g_onboarding_seen_path,",
            "std::ifstream product_state(g_product_state_path,",
            "std::ofstream replay(\n            stored_path +",
            "std::filesystem::exists(root.save_root,",
            "std::filesystem::create_directories(root.save_root,",
        ):
            self.assertNotIn(raw, source)

    def test_product_hosts_preserve_absolute_user_data_roots(self):
        for name in ("uniracers_modern_host.cpp", "completed_run_browser_host.cpp"):
            source = (ROOT / "native" / "product" / name).read_text(
                encoding="utf-8")
            begin = source.index("std::string product_user_data_root() {")
            end = source.index("\n}", begin)
            function = source[begin:end]
            self.assertEqual(function.count("host_trim_user_data_root("), 2,
                             name)
            self.assertNotIn("root.pop_back()", function, name)

    def test_compiled_unicode_directory_file_roundtrip(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-host-utf8-io"
            subprocess.run([
                compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-I", str(ROOT / "native" / "product"),
                str(ROOT / "tests" / "native" / "modern_host_utf8_io_test.cpp"),
                "-o", str(exe),
            ], cwd=ROOT, check=True, timeout=90)
            subprocess.run([str(exe)], cwd=ROOT, check=True, timeout=30)


if __name__ == "__main__":
    unittest.main()
