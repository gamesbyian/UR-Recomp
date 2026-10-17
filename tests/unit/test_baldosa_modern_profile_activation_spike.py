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
                         "completed_run_record.cpp",
                         "baldosa_native_run_record_admission.cpp",
                         "baldosa_native_multiplayer_records_summary.cpp",
                         "multiplayer_match_catalog.cpp",
                         "multiplayer_match_summary.cpp",
                         "multiplayer_match_record.cpp",
                         "local_multiplayer_match_binding.cpp"):
                (product / name).write_text("/* synthetic product */\n")
            pending = probe.plan(game, root)
            self.assertEqual(len(pending), 3)
            self.assertNotIn("baldosa_native_modern_root.cpp", pending[1][2])
            self.assertIn("host_profile_store.cpp", pending[1][2])
            self.assertIn("host_profile_catalog.cpp", pending[1][2])
            self.assertIn("host_product_store.cpp", pending[1][2])
            self.assertIn("baldosa_native_run_record_admission.cpp", pending[1][2])
            self.assertIn("baldosa_native_multiplayer_records_summary.cpp", pending[1][2])
            self.assertIn("multiplayer_match_record.cpp", pending[1][2])
            self.assertIn("after_config", pending[0][2])
            self.assertIn("ur-baldosa-modern-profile-fixture", pending[1][2])
            staged_host = pending[2][2]
            self.assertEqual(staged_host.count("RtlWriteSram()"), 1)
            self.assertIn("ur_baldosa_modern_profile_before_native_save()", staged_host)
            self.assertIn("ur_baldosa_modern_profile_finish_native_save(native_saved)", staged_host)
            # The real original RtlWriteSram must complete before a QA-only
            # fatal boundary, and the typed CAS must not have run yet.
            self.assertEqual(
                staged_host.count("UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE"), 1)
            self.assertIn("_Exit(86);", staged_host)
            # Native save refusal must be visible to a player/launcher;
            # startup code 7 is reserved for before-first-frame recovery.
            self.assertEqual(staged_host.count("exit(8);"), 2)
            self.assertIn("UR-BALDOSA-SAVE-FAILED", staged_host)
            self.assertIn("Native save was refused before writing.", staged_host)
            self.assertIn("Native save could not complete.", staged_host)
            self.assertLess(
                staged_host.index("UR_BALDOSA_NATIVE_PROFILE CHECKPOINT rejected"),
                staged_host.index("exit(8);"))
            self.assertIn('strcmp(qa_profile, "1") == 0', staged_host)
            self.assertIn('strcmp(qa_mode, "modern") == 0', staged_host)
            self.assertIn('strcmp(qa_crash, "1") == 0', staged_host)
            self.assertLess(
                staged_host.index("int native_saved = RtlWriteSram();"),
                staged_host.index("QA_CRASH_AFTER_RAW_WRITE"))
            self.assertLess(
                staged_host.index("QA_CRASH_AFTER_RAW_WRITE"),
                staged_host.index("ur_baldosa_modern_profile_finish_native_save(native_saved)"))
            self.assertEqual(probe.patch_framework_save(staged_host), staged_host)

            self.assertIn("int native_saved = RtlWriteSram();", staged_host)
            self.assertIn("int save_policy = ur_baldosa_modern_profile_before_native_save();", staged_host)
            self.assertIn("if (save_policy == 2)", staged_host)
            source_bridge = (
                Path(__file__).resolve().parents[2] /
                "tools/baldosa_modern_profile_activation.cpp").read_text()
            for proof in (
                "g_owned_next_boot_profile_id",
                "if (selected.selected()) g_owned_next_boot_profile_id",
                "exact_owned_next_boot_unchanged_under_lock",
                "BaldosaSramCheckpointStatus::SelectionConflict",
                "baldosa_sram_entry_missing(",
                "OWN_NEXT_BOOT_UNCHANGED",
                "return 2;  // original native wrapper SKIPS raw + typed writes",
            ):
                self.assertIn(proof, source_bridge)
            self.assertIn("OWN_NEXT_BOOT_CLEAN_QUIT raw_write_skipped=1 typed_write_skipped=1", staged_host)
            self.assertIn("else if (save_policy == 1)", staged_host)
            self.assertLess(staged_host.index("if (save_policy == 2)"), staged_host.index("RtlWriteSram();"))
            self.assertLess(staged_host.index("if (save_policy == 1)"), staged_host.index("RtlWriteSram();"))
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
