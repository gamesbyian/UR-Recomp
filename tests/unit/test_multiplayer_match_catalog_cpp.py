import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class MultiplayerMatchCatalogCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "multiplayer-match-catalog-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(ROOT / "native" / "product"),
                    "-I", str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "product" / "modern_racer_identity.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_runtime.cpp"),
                    str(ROOT / "native" / "product" / "host_product_state.cpp"),
                    str(ROOT / "native" / "product" / "output_resolution_policy.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_record.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_store.cpp"),
                    str(ROOT / "native" / "product" / "local_multiplayer_match_binding.cpp"),
                    str(ROOT / "native" / "product" / "multiplayer_match_record.cpp"),
                    str(ROOT / "native" / "product" / "multiplayer_match_catalog.cpp"),
                    str(ROOT / "tests" / "native" / "multiplayer_match_catalog_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)

    def test_catalog_never_follows_run_or_sidecar_links(self):
        src = (ROOT / "native" / "product" /
               "multiplayer_match_catalog.cpp").read_text(encoding="utf-8")
        self.assertIn("entry.symlink_status(", src)
        self.assertIn("std::filesystem::symlink_status(", src)
        self.assertIn("multiplayer_match_record_path_for_run(", src)
        self.assertIn("MatchMissingOrUnreadable", src)
        self.assertIn("RunUnreadable", src)


if __name__ == "__main__":
    unittest.main()
