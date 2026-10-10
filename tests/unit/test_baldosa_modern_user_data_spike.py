#!/usr/bin/env python3
"""The pinned Baldosa user-root port is opt-in, fail-closed and idempotent."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_modern_user_data_spike as port


class BaldosaModernUserDataRootTests(unittest.TestCase):
    def test_source_patches_preserve_stock_behavior_and_add_explicit_fail_closed_root(self):
        host = (
            "static int dir_is_writable(const char *dir) {\n"
            "char probe[1024];\n" + port.HOST_PROBE + "\nreturn 1;\n}\n"
            "int snesrecomp_anchor_to_exe_dir(void) {\n"
            "char dir[1024];\n" + port.HOST_ANCHOR + "\nreturn 1;\n}\n"
        )
        result = port.patch_host_paths(host)
        self.assertEqual(port.patch_host_paths(result), result)
        self.assertIn("getenv(\"SNESRECOMP_USER_DATA_DIR\")", result)
        self.assertIn("get_exe_dir(dir, sizeof(dir))", result)
        self.assertIn("if (dir[0] != '/') return 0", result)
        self.assertIn("if (!drive && !unc) return 0", result)
        self.assertIn("%s%s.snesrecomp_write_probe", result)
        self.assertNotIn('"%s.snesrecomp_write_probe",', result)
        with self.assertRaisesRegex(ValueError, "diverged"):
            port.patch_host_paths(host.replace(port.HOST_PROBE, ""))

        bind = port.KEYBIND_ANCHOR + "strcpy(s_ini_path, \"keybinds.ini\");\n}"
        bound = port.patch_keybinds(bind)
        self.assertEqual(port.patch_keybinds(bound), bound)
        self.assertIn("getenv(\"SNESRECOMP_USER_DATA_DIR\")", bound)
        self.assertIn("if (!exe_path || !*exe_path)", bound)
        with self.assertRaisesRegex(ValueError, "diverged"):
            port.patch_keybinds(bind.replace(port.KEYBIND_ANCHOR, ""))

        main = port.HOST_MAIN_CONFIG + "\n" + port.HOST_MAIN_CALL + "\n}"
        bridged = port.patch_host_main(main)
        self.assertEqual(port.patch_host_main(bridged), bridged)
        self.assertIn("UR-STARTUP-SAVE-ROOT:", bridged)
        self.assertIn("return 7;", bridged)
        self.assertIn("!snesrecomp_anchor_to_exe_dir()", bridged)
        self.assertIn("? 1 : snesrecomp_anchor_to_exe_dir()", bridged)
        with self.assertRaisesRegex(ValueError, "diverged"):
            port.patch_host_main(main.replace(port.HOST_MAIN_CALL, ""))

    def test_missing_pinned_host_file_does_not_mutate_any_file(self):
        with tempfile.TemporaryDirectory() as d:
            game = Path(d)
            host = game / "snesrecomp/runner/src/host_paths.c"
            host.parent.mkdir(parents=True)
            original = port.HOST_PROBE + "\n" + port.HOST_ANCHOR
            host.write_text(original, encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                port.plan(game)
            self.assertEqual(host.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
