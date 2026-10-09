import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class ModernProfileFlowCppTests(unittest.TestCase):
    def test_two_profile_fresh_process_identity_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "modern-profile-flow"
            subprocess.run([
                "g++","-std=c++17","-Wall","-Wextra","-Werror","-pedantic",
                "-I",str(ROOT/"native"/"product"),
                str(ROOT/"native"/"product"/"host_product_state.cpp"),
                str(ROOT/"native"/"product"/"output_resolution_policy.cpp"),
                str(ROOT/"native"/"product"/"modern_racer_identity.cpp"),
                str(ROOT/"native"/"product"/"clean_stock_sram.cpp"),
                str(ROOT/"native"/"product"/"host_profile_state.cpp"),
                str(ROOT/"native"/"product"/"host_profile_store.cpp"),
                str(ROOT/"native"/"product"/"host_profile_catalog.cpp"),
                str(ROOT/"native"/"product"/"host_profile_runtime.cpp"),
                str(ROOT/"native"/"product"/"completed_run_record.cpp"),
                str(ROOT/"native"/"product"/"completed_run_store.cpp"),
                str(ROOT/"tests"/"native"/"modern_profile_flow_test.cpp"),
                "-o",str(exe)
            ], cwd=ROOT, check=True)
            state_dir = pathlib.Path(tmp) / "state"
            subprocess.run([str(exe),"bootstrap",str(state_dir)], cwd=ROOT, check=True)
            subprocess.run([str(exe),"fresh",str(state_dir)], cwd=ROOT, check=True)
            # The C++ fixture refuses to read/overwrite a corrupted catalog
            # resized to 32 MiB. Preserve the canonical rejected file across
            # process exit without silently resetting the profile roster.
            oversized = state_dir / "oversized.catalog"
            self.assertEqual(oversized.stat().st_size, 32 * 1024 * 1024)

if __name__ == "__main__":
    unittest.main()
