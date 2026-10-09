#!/usr/bin/env python3
"""Pinned-host edit contract, without network, ROM, or CMake build."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_product_execution_spike as spike


class ProductSeamTests(unittest.TestCase):
    def setUp(self):
        self.main = (
            "/* UR_BALDOSA_GUEST_SNAPSHOT_BRIDGE */\n"
            "static const SnesDesktopHostGame kGameHost = {\n"
            "    .game_info           = &kGameInfo,\n"
            "    .num_players         = 2,\n"
            "#ifdef __EMSCRIPTEN__\n"
            "    .filter_frame_inputs = WebNetplayFilterInputs,\n"
            "#endif\n"
            "};\n"
        )

    def test_host_hook_is_guarded_and_idempotent(self):
        staged = spike.patch_main(self.main)
        self.assertEqual(staged.count(spike.MARK), 1)
        self.assertIn("ur_baldosa_product_filter_frame_inputs", staged)
        self.assertIn(".filter_frame_inputs = WebNetplayFilterInputs", staged)
        self.assertIn("#ifndef __EMSCRIPTEN__", staged)
        self.assertEqual(spike.patch_main(staged), staged)
        self.assertEqual(spike.patch_main(staged).count(
            ".filter_frame_inputs"), 2)

    def test_refuses_unverified_main(self):
        with self.assertRaisesRegex(ValueError, "verified"):
            spike.patch_main(self.main.replace(spike.OBSERVER, "NOT_OBSERVER"))
        with self.assertRaisesRegex(ValueError, "Unrecognized"):
            spike.patch_main(self.main.replace("    .num_players         = 2,\n", ""))

    def test_appends_one_source_without_deleting_any_existing_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            (root / "native/product").mkdir(parents=True)
            (root / "tools/baldosa_native_product_execution.cpp").write_text("// shim")
            (root / "native/product/baldosa_execution_backend.hpp").write_text("// API")
            cmake = ("add_executable(UniracersSNESRecomp src/main.c)\n"
                     "# UR_BALDOSA_GUEST_SNAPSHOT_BRIDGE\n"
                     "# UR_BALDOSA_NATIVE_RACER_PRESENTATION\n")
            staged = spike.patch_cmake(cmake, root)
            self.assertTrue(staged.startswith(cmake))
            self.assertEqual(staged.count(spike.MARK), 1)
            self.assertEqual(spike.patch_cmake(staged, root), staged)
            self.assertIn("target_sources(UniracersSNESRecomp PRIVATE", staged)
            with self.assertRaisesRegex(ValueError, "verified"):
                spike.patch_cmake("cmake_minimum_required(VERSION 3.20)", root)


if __name__ == "__main__":
    unittest.main()
