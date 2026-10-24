#!/usr/bin/env python3
"""Source contracts for coexisting Modern title and native SDL controller journeys.

This guards the *draft integration source*, not physical hardware or a Windows
release gate. Exact-head Windows acceptance remains necessary after rebase.
"""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[2] /
          "tools/baldosa_native_modern_root.cpp").read_text(encoding="utf-8")


def require_lifecycle(source: str) -> None:
    for token in (
        "snesrecomp_desktop_product_seat_source(int seat)",
        "snesrecomp_desktop_product_seat_move(int from, int to)",
        "bool join_p2_owner_present()",
        "if (!join_p2_owner_present()) return false;",
        "join_watch_seat_owners();",
        "join_return_moved_pad();",
        "promote_lone_seat2_pad();",
        "g_join_p1_by_keyboard = true;",
        "g_join_moved_source = snesrecomp_desktop_product_seat_source(1);",
        "join_pad_moved from=1 to=2",
        "join_seat_left seat=2 confirmation_cleared=1",
        "lone_pad_promoted from=2 to=1",
    ):
        if token not in source:
            raise AssertionError("lost merged-main controller behavior: " + token)


class ModernTitleControllerReconciliation(unittest.TestCase):
    def test_merged_controller_lifecycle_is_present(self):
        require_lifecycle(SOURCE)

    def test_negative_removal_controls(self):
        for token in ("if (!join_p2_owner_present()) return false;",
                      "g_join_p1_by_keyboard = true;",
                      "join_watch_seat_owners();"):
            with self.subTest(token=token), self.assertRaises(AssertionError):
                require_lifecycle(SOURCE.replace(token, ""))

    def test_title_and_controller_smoke_ids_do_not_collide(self):
        title = SOURCE.split('const char* fixture = std::getenv("UR_BALDOSA_MODERN_ROOT_KEY_SMOKE");', 1)[1]
        title = title.split("g_title_logged = false;", 1)[0]
        for mode in range(15, 20):
            self.assertIn('std::strcmp(opt, "' + str(mode) + '")', SOURCE)
            self.assertNotIn('std::strcmp(fixture, "' + str(mode) + '")', title)
        for mode in range(24, 29):
            self.assertIn('std::strcmp(opt, "' + str(mode) + '")', SOURCE)
            self.assertIn('std::strcmp(fixture, "' + str(mode) + '")', title)
        self.assertIn("SDL_AttachVirtualJoystick(&desc)", SOURCE)

    def test_title_confirm_and_original_attract_wake_remain(self):
        self.assertIn("confirm_modern_native_title();", SOURCE)
        self.assertIn("wake_original_stock_attract();", SOURCE)
        self.assertIn("g_original_attract_p2_release_button", SOURCE)

    def test_p2_reentry_is_gated_by_observed_stock_main(self):
        start = SOURCE.index("// During stock gameplay P2 remains P2.")
        end = SOURCE.index("if (player != 0) return 0;", start)
        body = SOURCE[start:end]
        self.assertIn("snesrecomp_desktop_product_seat_source(0) != -1", body)
        self.assertIn("snesrecomp_desktop_product_seat_source(1) == -1", body)
        self.assertIn("reopen_on_observed_stock_main()", body)


if __name__ == "__main__":
    unittest.main()
