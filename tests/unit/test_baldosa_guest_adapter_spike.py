"""The Baldosa guest adapter is deterministic, revision-guarded and idempotent."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "baldosa_guest_bridge", ROOT / "tools/baldosa_guest_adapter_spike.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class BaldosaGuestAdapterTest(unittest.TestCase):
    def test_host_guard_and_idempotence(self):
        source = (
            "#include \"host_main.h\"\n"
            "static const SnesDesktopHostGame kGameHost = {\n"
            "    .game_info           = &kGameInfo,\n"
            "};\n"
        )
        patched = mod.patch_main(source)
        self.assertEqual(patched.count(mod.FIELD), 1)
        self.assertEqual(patched.count(mod.PROTOTYPE), 1)
        self.assertEqual(mod.patch_main(patched), patched)
        with self.assertRaises(ValueError):
            mod.patch_main("#include \"host_main.h\"\n")

    def test_build_wiring_only_adds_actual_ur_snapshot_sources(self):
        base = "snesrecomp_target_desktop_host(UniracersSNESRecomp)\n"
        with tempfile.TemporaryDirectory() as td:
            patched = mod.patch_cmake(base, Path(td))
            self.assertEqual(mod.patch_cmake(patched, Path(td)), patched)
            self.assertIn("native/presentation/racer_guest_snapshot.cpp", patched)
            self.assertIn("native/presentation/racer_replacement_selector.cpp", patched)
            self.assertNotIn("SNESRECOMP_ENABLE_MODS OFF", patched)
            with self.assertRaises(ValueError):
                mod.patch_cmake("add_executable(foo main.c)\n", Path(td))


if __name__ == "__main__":
    unittest.main()
