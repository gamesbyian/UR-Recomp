import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
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
        return subprocess.run(["g++", *args], capture_output=True, text=True, env=env, cwd=cwd, timeout=60)

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


    def test_corrupted_object_stderr_receipt_and_interrupted_save_recompile(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.cpp").write_text(
                "int helper(); int main(){return helper()==7?0:1;}\n")
            (root / "b.cpp").write_text("int helper(){return 7;}\n")
            cache = root / "cache"
            def check():
                r = self.run_shim(cache, "-std=c++17", "a.cpp", "b.cpp",
                                  "-o", "app", cwd=root)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(subprocess.run([str(root / "app")]).returncode, 0)
                return r
            check()
            objs = sorted(cache.glob("*.o"))
            self.assertEqual(len(objs), 2)
            obj = objs[0]
            receipt = cache / (obj.stem + ".receipt.json")
            err = cache / (obj.stem + ".err")
            self.assertTrue(receipt.is_file())
            self.assertEqual(json.loads(receipt.read_text())["object_sha256"],
                             hashlib.sha256(obj.read_bytes()).hexdigest())
            # Merely retaining the content-addressed filename is insufficient.
            obj.write_bytes(b"invalid native object")
            check()
            self.assertNotEqual(obj.read_bytes(), b"invalid native object")
            self.assertEqual(json.loads(receipt.read_text())["object_sha256"],
                             hashlib.sha256(obj.read_bytes()).hexdigest())
            # Damaged compiler diagnostics are not replayed as a valid hit.
            err.write_bytes(b"forged compiler diagnostics")
            self.assertNotIn("forged compiler diagnostics", check().stderr)
            self.assertNotEqual(err.read_bytes(), b"forged compiler diagnostics")
            # A manifest corruption and an interrupted save each force
            # source recompilation without accepting a partially written .o.
            receipt.write_text('{"schema":"untrusted"}')
            check()
            # Even a byte-perfect object/diagnostics bundle cannot be
            # repurposed under a different source-preprocessor key.
            manifest = json.loads(receipt.read_text())
            manifest["key"] = "0" * 64
            receipt.write_text(json.dumps(manifest))
            check()
            self.assertEqual(json.loads(receipt.read_text())["key"], obj.stem)
            receipt.unlink()
            obj.write_bytes(b"truncated")
            check()
            self.assertEqual(json.loads(receipt.read_text())["object_sha256"],
                             hashlib.sha256(obj.read_bytes()).hexdigest())

    def test_simultaneous_writers_never_share_staging_filenames(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.cpp").write_text(
                "int helper(); int main(){return helper()==7?0:1;}\n")
            (root / "b.cpp").write_text("int helper(){return 7;}\n")
            # Pre-create shim to eliminate an unrelated symlink creation race.
            shim = root / "shim"
            shim.mkdir()
            (shim / "g++").symlink_to(ROOT / "tools/ci_compile_cache.py")
            cache = root / "cache"
            def compile_one(index):
                return self.run_shim(cache, "-std=c++17", "a.cpp", "b.cpp",
                                     "-o", f"app{index}", cwd=root)
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(compile_one, range(2)))
            for index, result in enumerate(results):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    subprocess.run([str(root / f"app{index}")]).returncode, 0)
            # Same-key writers may interleave the final object and receipt
            # replaces; a subsequent consumer must detect any mismatch,
            # recompile from source and leave verifiably consistent entries.
            result = self.run_shim(cache, "-std=c++17", "a.cpp", "b.cpp",
                                   "-o", "app-verified", cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(subprocess.run(
                [str(root / "app-verified")]).returncode, 0)
            for obj in cache.glob("*.o"):
                receipt = cache / (obj.stem + ".receipt.json")
                self.assertTrue(receipt.is_file())
                observed = json.loads(receipt.read_text())
                self.assertEqual(observed["object_sha256"],
                                 hashlib.sha256(obj.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
