"""Prevent drift in the first UR-Recomp-to-Baldosa native host adapter."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "baldosa_adapter", ROOT / "tools/baldosa_guest_snapshot_adapter.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AdapterTest(unittest.TestCase):
    def test_main_additive_and_idempotent(self):
        original = (
            '#include "host_main.h"\n'
            "static const SnesDesktopHostGame kGameHost = {\n"
            "    .game_info           = &kGameInfo,\n"
            "};\n"
        )
        result = mod.patched_main(original)
        self.assertIn(".after_run_frame = &ur_baldosa_racer_snapshot_after_frame", result)
        self.assertEqual(mod.patched_main(result), result)
        self.assertIn("&kGameInfo", result)

    def test_host_contract_changes_fail_closed(self):
        with self.assertRaises(ValueError):
            mod.patched_main("static const Foo kGameHost = {\n};")

    def test_cmake_reuses_first_party_sources(self):
        s = mod.patched_cmake("add_executable(UniracersSNESRecomp src/main.c)\n", ROOT)
        self.assertIn("native/presentation/racer_guest_snapshot.cpp", s)
        self.assertIn("native/presentation/racer_replacement_selector.cpp", s)
        self.assertIn("cxx_std_17", s)
        self.assertEqual(s, mod.patched_cmake(s, ROOT))


if __name__ == "__main__":
    unittest.main()
