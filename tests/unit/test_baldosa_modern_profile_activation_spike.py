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
            source.parent.mkdir(parents=True)
            body = ("/* " + probe.NATIVE_MARK + " */\n"
                    + probe.MAIN_HOST + probe.MAIN_PAUSE + "};\n")
            source.write_text(body)
            cmake.write_text("# " + probe.NATIVE_MARK + "\n")
            with self.assertRaises(ValueError):
                probe.plan(game, root)
            self.assertEqual(source.read_text(), body)
            self.assertEqual(cmake.read_text(), "# " + probe.NATIVE_MARK + "\n")

            product = root / "native/product"
            product.mkdir(parents=True)
            bridge = root / "tools/baldosa_modern_profile_activation.cpp"
            bridge.parent.mkdir(parents=True)
            bridge.write_text("/* synthetic unit bridge */\n")
            for name in probe.SOURCES:
                (product / name).write_text("/* synthetic product */\n")
            pending = probe.plan(game, root)
            self.assertEqual(len(pending), 2)
            self.assertIn("host_profile_store.cpp", pending[1][2])
            self.assertIn("host_profile_catalog.cpp", pending[1][2])
            self.assertIn("host_product_store.cpp", pending[1][2])
            self.assertIn("after_config", pending[0][2])
            with self.assertRaisesRegex(ValueError, "must already be staged"):
                probe.patch_cmake("add_library(other INTERFACE)\n", root)


if __name__ == "__main__":
    unittest.main()
