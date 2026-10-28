#!/usr/bin/env python3
"""Current-main Modern title graft: guard existing player routes during integration."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ModernTitleCurrentMainIntegration(unittest.TestCase):
    def test_title_and_existing_player_guards_share_one_root(self):
        source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        for required in (
            '#include "modern_title_presenter.hpp"',
            "modern_user_data_root()",
            "baldosa_options_path(user_root).u8string()",
            "g_join_p1_by_keyboard = true",
            "g_run_save_feedback,",
            "render_modern_title(",
            "ur_baldosa_modern_root_prepare_frame(",
            "ur_baldosa_modern_root_window_base_width(",
            "original_stock_attract_source_ready()",
            'std::strcmp(opt, "19")',
            'std::strcmp(opt, "24")',
            "mode > 37",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_native_atlas_capture_uses_unicode_windows_filesystem_io(self):
        source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        capture = source.split("void capture_modern_title_native_frame(", 1)[1]
        capture = capture.split("\n}\n", 1)[0]
        # The opt-in atlas path must survive a non-ACP Windows username,
        # both on write and on failure cleanup. Receipts remain UTF-8.
        for required in (
            '_wgetenv(L"UR_BALDOSA_MODERN_TITLE_CAPTURE_DIR")',
            '_wfopen(file.c_str(), L"wb")',
            'std::filesystem::remove(file, remove_error)',
            'file.u8string()',
            'receipt_path_utf8.c_str()',
            'std::fopen(file.c_str(), "wb")',  # unchanged POSIX path
        ):
            with self.subTest(required=required):
                self.assertIn(required, capture)
        self.assertNotIn("std::fopen(file.string().c_str()", capture)
        self.assertNotIn("std::remove(file.string().c_str()", capture)

    def test_title_is_only_in_modern_host_adapter(self):
        source = (ROOT / "tools/baldosa_modern_profile_activation_spike.py").read_text()
        self.assertIn(".native_widescreen   = 1", source)
        self.assertIn("&ur_baldosa_modern_root_prepare_frame", source)
        self.assertIn("&ur_baldosa_modern_root_viewport", source)
        self.assertIn("iw != 342 || ih != 224", source)
        self.assertIn('if ".draw_frame" in source:', source)


if __name__ == "__main__":
    unittest.main()
