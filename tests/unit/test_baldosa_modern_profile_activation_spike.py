#!/usr/bin/env python3
"""Guard the upstream callback and existing profile components before staging."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_modern_profile_activation_spike as probe


class BaldosaModernProfileActivationStage(unittest.TestCase):
    def test_descriptor_callback_is_owned_by_existing_upstream_host(self):
        main = (
            '#include "host_main.h"\n'
            "/* " + probe.NATIVE_MARK + " */\n"
            + probe.MAIN_HOST + "    .build_version = SNES_GAME_VERSION,\n"
            + probe.MAIN_PAUSE + "};\n"
        )
        patched = probe.patch_main(main)
        self.assertEqual(probe.patch_main(patched), patched)
        self.assertIn("ur_baldosa_modern_profile_after_config", patched)
        self.assertIn(".after_config", patched)
        self.assertIn(".before_run_frame", patched)
        self.assertIn("ur_baldosa_modern_profile_before_run_frame", patched)
        self.assertIn(".draw_frame          = &ur_baldosa_modern_root_draw_frame", patched)
        self.assertIn("ur_baldosa_modern_root_after_config();", patched)
        with self.assertRaisesRegex(ValueError, "compositor"):
            probe.patch_main(main.replace(
                probe.MAIN_PAUSE,
                "    .draw_frame = &another_native_compositor,\n" +
                probe.MAIN_PAUSE))
        self.assertIn("exit(7);", patched)
        self.assertIn(probe.MAIN_PAUSE, patched)
        with self.assertRaisesRegex(ValueError, "pause seam"):
            probe.patch_main(main.replace(probe.NATIVE_MARK, ""))

    def test_cmake_reuses_existing_modern_components_and_is_atomic(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            game = root / "baldosa"
            source = game / "src/main.c"
            cmake = game / "CMakeLists.txt"
            framework = game / "snesrecomp/runner/src/desktop/host_main.c"
            framework.parent.mkdir(parents=True)
            source.parent.mkdir(parents=True)
            body = ("/* " + probe.NATIVE_MARK + " */\n"
                    + probe.MAIN_HOST + probe.MAIN_PAUSE + "};\n")
            source.write_text(body)
            cmake.write_text("# " + probe.NATIVE_MARK + "\n")
            original_shutdown = ("static void shutdown(void) {\n"
                                 + probe.FRAMEWORK_SAVE + "\n}\n")
            framework.write_text(original_shutdown)
            with self.assertRaises(ValueError):
                probe.plan(game, root)
            self.assertEqual(source.read_text(), body)
            self.assertEqual(cmake.read_text(), "# " + probe.NATIVE_MARK + "\n")

            product = root / "native/product"
            product.mkdir(parents=True)
            bridge = root / "tools/baldosa_modern_profile_activation.cpp"
            bridge.parent.mkdir(parents=True)
            bridge.write_text("/* synthetic unit bridge */\n")
            (root / "tools/baldosa_native_modern_root.cpp").write_text(
                "/* synthetic shared Modern root consumer */\n")
            (root / "tools/baldosa_modern_profile_native_fixture.cpp").write_text(
                "/* synthetic fixture */\n")
            for name in (*probe.SOURCES,
                         "baldosa_native_records_summary.cpp",
                         "completed_run_store.cpp",
                         "completed_run_record.cpp"):
                (product / name).write_text("/* synthetic product */\n")
            pending = probe.plan(game, root)
            self.assertEqual(len(pending), 3)
            self.assertNotIn("baldosa_native_modern_root.cpp", pending[1][2])
            self.assertIn("host_profile_store.cpp", pending[1][2])
            self.assertIn("host_profile_catalog.cpp", pending[1][2])
            self.assertIn("host_product_store.cpp", pending[1][2])
            self.assertIn("after_config", pending[0][2])
            self.assertIn("ur-baldosa-modern-profile-fixture", pending[1][2])
            staged_host = pending[2][2]
            self.assertEqual(staged_host.count("RtlWriteSram()"), 1)
            self.assertIn("ur_baldosa_modern_profile_before_native_save()", staged_host)
            self.assertIn("ur_baldosa_modern_profile_finish_native_save(native_saved)", staged_host)
            self.assertIn("int native_saved = RtlWriteSram();", staged_host)
            self.assertLess(staged_host.index("if (ur_baldosa_modern_profile_before_native_save())"), staged_host.index("RtlWriteSram();"))
            self.assertLess(staged_host.index("RtlWriteSram();"), staged_host.index("ur_baldosa_modern_profile_finish_native_save(native_saved)"))
            self.assertEqual(probe.patch_framework_save(staged_host), staged_host)
            self.assertEqual(framework.read_text(), original_shutdown)
            with self.assertRaisesRegex(ValueError, "shutdown boundary"):
                probe.patch_framework_save(original_shutdown.replace(
                    probe.FRAMEWORK_SAVE, "  RtlWriteSram();"))
            with self.assertRaisesRegex(ValueError, "shutdown boundary"):
                probe.patch_framework_save(original_shutdown + probe.FRAMEWORK_SAVE)
            with self.assertRaisesRegex(ValueError, "must already be staged"):
                probe.patch_cmake("add_library(other INTERFACE)\n", root)


if __name__ == "__main__":
    unittest.main()
