#!/usr/bin/env python3
"""Fail-closed source receipt tests for separately created native P1 and P2.

Synthetic strings never confer a real Windows or strict original event pass.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from baldosa_native_second_racer_probe import (
    require_p2_creation,
    require_actual_two_seat_go,
    require_native_p2_recovery,
    require_native_created_p1_pad_handler,
)


class SecondNativeRacerProofTests(unittest.TestCase):
    def test_two_canonical_profile_creation_receipts_no_live_swap(self):
        good = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
            "root=saves/profile-mike\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT second_racer_opened=1 preset=1 "
            "activation=next_process\n"
            "UR_BALDOSA_NATIVE_SECOND_RACER status=0 preset=1 id=andrew "
            "activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT second_racer_created=1 "
            "activation=next_process\n"
        )
        require_p2_creation(good)
        for bad in (
            good.replace("status=0", "status=2"),
            good.replace("id=andrew", "id=mike"),
            good.replace("preset=1", "preset=0"),
            good.replace("profile=mike", "profile=andrew"),
            good + good,
            good + "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew\n",
            good + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
        ):
            with self.subTest(bad=bad[-100:]):
                with self.assertRaises(ValueError):
                    require_p2_creation(bad)

    def test_new_racers_require_exact_native_gamepad_handler_edges(self):
        for mode, controls in (
            ("8", ("X", "A")),
            ("9", ("X", "DPAD_DOWN", "A")),
        ):
            good = "".join(
                f"UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad "
                f"mode={mode} button={button}\n" for button in controls)
            require_native_created_p1_pad_handler(good, mode)
            for bad in (
                good + good,
                good.replace("button=A", "button=X"),
                good.replace("mode=" + mode, "mode=7"),
                good.replace("button=X\n", "", 1),
                good + "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad "
                "mode=7 button=A\n",
            ):
                with self.subTest(mode=mode), self.assertRaises(ValueError):
                    require_native_created_p1_pad_handler(bad, mode)

    def test_interrupted_p2_catalog_requires_real_controller_source_recovery(self):
        # Source-log fixture only; no actual original guest or OS crash.
        good = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
            "root=saves/profile-mike\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT second_racer_opened=1 preset=1 "
            "activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 button=X\n"
            "UR_BALDOSA_MODERN_ROOT second_racer_preset=2\n"
            "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 "
            "button=DPAD_DOWN\n"
            "UR_BALDOSA_NATIVE_SECOND_RACER_RECOVERY restored=1 "
            "catalog_only=1 p1_unchanged=1 activation=next_process\n"
            "UR_BALDOSA_NATIVE_SECOND_RACER status=4 preset=2 "
            "id=martin activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT second_racer_created=1 "
            "activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 button=A\n"
        )
        require_native_p2_recovery(good)
        failures = (
            good.replace("status=4", "status=0"),
            good.replace("status=4", "status=2"),
            good.replace("id=martin", "id=andrew"),
            good.replace("catalog_only=1", "catalog_only=0"),
            good.replace("p1_unchanged=1", "p1_unchanged=0"),
            good.replace("preset=2", "preset=1"),
            good.replace("button=DPAD_DOWN", "button=DPAD_UP"),
            good.replace("mode=9 button=A", "mode=8 button=A"),
            good.replace("status=4", "status=4") + good,
            good.replace(
                "UR_BALDOSA_NATIVE_SECOND_RACER_RECOVERY restored=1 "
                "catalog_only=1 p1_unchanged=1 activation=next_process\n", ""),
            good.replace(
                "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 "
                "button=DPAD_DOWN\n", ""),
            good + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
            good + "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n",
            good + "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=martin\n",
        )
        for bad in failures:
            with self.subTest(reason=bad[-90:]), self.assertRaises(ValueError):
                require_native_p2_recovery(bad)

    def test_two_distinct_confirmed_seats_before_real_stock_handoff(self):
        good = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
            "root=saves/profile-mike\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2\n"
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1\n"
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2\n"
            "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n"
        )
        require_actual_two_seat_go(good)
        for bad in (
            good.replace("seat=2", "seat=1"),
            good.replace("players=2 menu=3d", "players=1 menu=3c"),
            good.replace("profile=mike", "profile=andrew"),
            good + good,
            good.replace("join_confirmed seat=2\n", ""),
            good + "UR_BALDOSA_MODERN_ROOT unbound_2p_consented=1\n",
            good + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
        ):
            with self.subTest(bad=bad[-100:]):
                with self.assertRaises(ValueError):
                    require_actual_two_seat_go(bad)

    def test_actual_modal_stays_product_owned_with_p1_reboot_barrier(self):
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        adapter = (ROOT / "tools/baldosa_modern_profile_activation.cpp").read_text()
        presenter = (ROOT / "native/product/modern_root_overlay_presenter.hpp"
                     ).read_text()
        for token in (
            "g_ever_entered_stock",
            "ur_baldosa_modern_create_second_preset(",
            "second_racer_opened=1",
            "second_racer_created=1",
            "g_named_profile_stale = true;",
            'std::strcmp(opt, "5") == 0',
        ):
            self.assertIn(token, root)
        self.assertIn("create_baldosa_second_preset_for_next_boot", adapter)
        self.assertIn("SECOND RACER", presenter)
        self.assertNotIn("SECOND STOCK RACER", presenter)
        self.assertNotIn("RtlWriteSram(", root)


if __name__ == "__main__":
    unittest.main()
