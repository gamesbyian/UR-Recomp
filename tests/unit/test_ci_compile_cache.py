import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import ci_compile_cache as cc

ROOT = Path(__file__).resolve().parents[2]


class ParseTests(unittest.TestCase):
    def test_splits_compile_and_link_inputs(self):
        sources, cflags, lflags, out = cc.parse(
            ["-std=c++17", "-I", "inc", "a.cpp", "b.c", "x.o", "-lm", "-pthread", "-o", "bin"])
        self.assertEqual(sources, ["a.cpp", "b.c"])
        self.assertEqual(cflags, ["-std=c++17", "-I", "inc", "-pthread"])
        self.assertEqual(lflags, ["-std=c++17", "x.o", "-lm", "-pthread"])
        self.assertEqual(out, "bin")

    def test_ineligible_commands_pass_through(self):
        for args in (["-c", "a.cpp", "-o", "a.o"], ["a.cpp"], ["@rsp", "-o", "x"],
                     ["-fsanitize=address", "a.cpp", "-o", "x"], ["-o", "x", "-x", "c++", "a.cpp"]):
            self.assertIsNone(cc.parse(args), args)


@unittest.skipUnless(shutil.which("g++"), "g++ unavailable")
class ShimBehaviourTests(unittest.TestCase):
    def run_shim(self, cache, *args, cwd):
        shim = Path(cwd) / "shim"
        shim.mkdir(exist_ok=True)
        link = shim / "g++"
        if not link.exists():
            link.symlink_to(ROOT / "tools/ci_compile_cache.py")
        env = dict(os.environ, PATH=f"{shim}{os.pathsep}{os.environ['PATH']}",
                   UR_COMPILE_CACHE_DIR=str(cache))
        return subprocess.run(["g++", *args], capture_output=True, text=True, env=env, cwd=cwd)

    def test_hit_miss_edit_and_error_semantics(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "a.cpp").write_text('int helper(); int main(){return helper()==7?0:1;}\n')
            (d / "b.cpp").write_text("int helper(){return 7;}\n")
            cache = d / "cache"
            for _ in range(2):  # miss then hit
                r = self.run_shim(cache, "-std=c++17", "a.cpp", "b.cpp", "-o", "app", cwd=d)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(subprocess.run([str(d / "app")]).returncode, 0)
            self.assertEqual(len(list(cache.glob("*.o"))), 2)
            # An edit must change the key and the behaviour (no stale object).
            (d / "b.cpp").write_text("int helper(){return 8;}\n")
            r = self.run_shim(cache, "-std=c++17", "a.cpp", "b.cpp", "-o", "app", cwd=d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(subprocess.run([str(d / "app")]).returncode, 1)
            # Compile errors surface with a nonzero status and are not cached.
            (d / "b.cpp").write_text("int helper(){ return ; }\n")
            before = len(list(cache.glob("*.o")))
            r = self.run_shim(cache, "-std=c++17", "a.cpp", "b.cpp", "-o", "app2", cwd=d)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(len(list(cache.glob("*.o"))), before)


if __name__ == "__main__":
    unittest.main()
