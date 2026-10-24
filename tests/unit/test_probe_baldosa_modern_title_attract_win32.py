"""Negative tests for observed, not fabricated, first original idle attract cycle."""
import unittest
from tools.probe_baldosa_modern_title_attract_win32 import (
    verify_original_source_attract, verify_source_driven_preview,
    verify_original_guest_presentations, verify_source_driven_recovery,
    verify_named_original_play_after_recovery)

OPEN = "UR_BALDOSA_MODERN_ROOT opened=1"
MAIN = "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=main_menu frame=440 menu=d7 race=00 overlay_title=1"
TITLE = "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=attract_title frame=943 menu=84 race=00 overlay_title=1"
DEMO = "UR_MODERN_TITLE_ORIGINAL_SOURCE phase=demo_race frame=1532 menu=00 race=01 overlay_title=1"


class StockIdleAttractWitnessTest(unittest.TestCase):
    def test_valid_stock_source_cycle_and_no_automatic_visible_credit(self):
        self.assertEqual(
            [x["frame"] for x in verify_original_source_attract(
                "\n".join((OPEN, MAIN, TITLE, DEMO)))],
            [440, 943, 1532])

    def test_source_driven_original_preview_requires_real_wake_separation(self):
        steps = (
            OPEN,
            MAIN,
            TITLE,
            "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=943 menu=84 focus=host guest_writes=0",
            DEMO.replace("overlay_title=1", "overlay_title=0"),
            "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600 guest_writes=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT p1_wake_consumed=1 frame=1600 race=01",
            "UR_MODERN_TITLE_STOCK_ATTRACT stable_title=1 frame=1640 root_unselected=1",
            "UR_MODERN_TITLE_STOCK_ATTRACT separate_confirm=1 frame=1660",
            "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=1674 input_owned=1",
            "UR_MODERN_TITLE_STOCK_ATTRACT reached_root=1 frame=1690 no_stock_route=1",
        )
        good = "\n".join(steps)
        assert len(verify_source_driven_preview(good)) == 3
        for index in range(1, len(steps)):
            bad = "\n".join(x for i, x in enumerate(steps) if i != index)
            with self.subTest(index=index), self.assertRaises(ValueError):
                verify_source_driven_preview(bad)
        with self.assertRaisesRegex(ValueError, "source guest lifecycle"):
            verify_source_driven_preview(
                good.replace("overlay_title=0", "overlay_title=1"))
        with self.assertRaisesRegex(ValueError, "wake"):
            verify_source_driven_preview(good.replace(
                "separate_confirm=1 frame=1660",
                "separate_confirm=1 frame=1640"))

    def test_keyboard_and_unjoined_p2_wake_cannot_take_p1_root_input(self):
        common = (
            OPEN, MAIN, TITLE,
            "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=943 menu=84 focus=host guest_writes=0",
            DEMO.replace("overlay_title=1", "overlay_title=0"),
            "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600 guest_writes=0",
        )
        end = (
            "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=1674 input_owned=1",
            "UR_MODERN_TITLE_STOCK_ATTRACT reached_root=1 frame=1690 no_stock_route=1",
        )
        for route, first, confirm in (
            ("keyboard",
             "UR_MODERN_TITLE_STOCK_ATTRACT keyboard_wake_consumed=1 frame=1600",
             "UR_MODERN_TITLE_STOCK_ATTRACT separate_keyboard_confirm=1 frame=1660"),
            ("p2",
             "UR_MODERN_TITLE_STOCK_ATTRACT p2_wake_consumed=1 frame=1600",
             "UR_MODERN_TITLE_STOCK_ATTRACT p2_then_p1_confirm=1 frame=1660"),
        ):
            release = (
                ("UR_MODERN_TITLE_STOCK_ATTRACT p2_wake_release_consumed=1 frame=1602",)
                if route == "p2" else ())
            good = "\n".join((*common, first, *release, confirm, *end))
            with self.subTest(route=route):
                self.assertEqual(len(verify_source_driven_preview(
                    good, wake_route=route)), 3)
                for wrong_route in {"p1", "keyboard", "p2"} - {route}:
                    with self.assertRaisesRegex(ValueError, "wake"):
                        verify_source_driven_preview(good, wake_route=wrong_route)
                with self.assertRaisesRegex(ValueError, "wake"):
                    verify_source_driven_preview(
                        good.replace(confirm, confirm.replace("=1", "=0")),
                        wake_route=route)
                if route == "p2":
                    with self.assertRaisesRegex(ValueError, "wake"):
                        verify_source_driven_preview(good.replace(
                            "p2_wake_release_consumed=1",
                            "p2_wake_release_consumed=0"), wake_route="p2")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            verify_source_driven_preview("\n".join(common), wake_route="unknown")

    def test_genuine_main_source_recovery_is_distinct_from_wake(self):
        good = "\n".join((
            OPEN, MAIN, TITLE,
            "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=943 menu=84 focus=host guest_writes=0",
            DEMO.replace("overlay_title=1", "overlay_title=0"),
            "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600 guest_writes=0",
            "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=1674 input_owned=1",
            "UR_MODERN_TITLE_STOCK_ATTRACT play_deferred=1 frame=1710 source_menu=00 source_race=01 guest_writes=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT native_play_denied=1 frame=1710 profile_stale=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT play_deferred=1 frame=3770 source_menu=d7 source_race=00 guest_writes=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT native_play_denied_settling=1 frame=3770 menu=d7 guest_writes=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT source_main_recovered=1 frame=3818 menu=d7 race=00 stable=60 guest_writes=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT play_rearmed=1 frame=3900 source_main=d7 stable=60 guest_writes=0",
        ))
        result = verify_source_driven_recovery(good)
        self.assertEqual([item["frame"] for item in result], [1710, 3770, 3818, 3900])
        for bad in (
            good.replace("frame=3818", "frame=1711"),
            good.replace("frame=3818", "frame=3841"),
            good.replace("stable=60", "stable=2"),
            good.replace("native_play_denied_settling=1", "native_play_denied_settling=0"),
            good.replace("menu=d7 race=00 stable=60 guest_writes=0",
                         "menu=d7 race=01 stable=60 guest_writes=0"),
            good.replace("native_play_denied=1", "native_play_denied=0"),
            good.replace("play_rearmed=1", "play_rearmed=0"),
            good.replace("frame=3900", "frame=3800"),
            good + "\\nUR_BALDOSA_MODERN_ROOT stock_requested players=1",
            good + "\\nUR_BALDOSA_MODERN_ROOT active_profile_stale=1",
            good + "\\nUR_MODERN_TITLE_STOCK_ATTRACT source_main_recovered=1 frame=3818 menu=d7 race=00 stable=60 guest_writes=0",
        ):
            with self.subTest(bad=bad[-110:]), self.assertRaises(ValueError):
                verify_source_driven_recovery(bad)

    def test_real_named_profile_after_source_recovery_requires_stock_one_player(self):
        stages = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
            MAIN.replace("frame=440", "frame=437"),
            TITLE.replace("frame=943", "frame=940"),
            "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=940 menu=84 focus=host guest_writes=0",
            DEMO.replace("frame=1532", "frame=1529").replace("overlay_title=1", "overlay_title=0"),
            "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600 guest_writes=0",
            "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=1674 input_owned=1",
            "UR_MODERN_TITLE_STOCK_ATTRACT named_play_denied=1 frame=1710 source_admitted=0 guest_writes=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT named_play_denied=1 frame=3770 source_admitted=0 guest_writes=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT source_main_recovered=1 frame=3815 menu=d7 race=00 stable=60 guest_writes=0",
            "UR_MODERN_TITLE_STOCK_ATTRACT named_play_requested=1 frame=3900 source_main=d7 source_stable=60",
            "UR_BALDOSA_MODERN_ROOT stock_requested players=1",
            "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
        )
        good = "\n".join(stages)
        result = verify_named_original_play_after_recovery(good)
        self.assertEqual(result[-1]["phase"], "original_stock_one_player_entered")
        self.assertEqual(result[2], {"phase": "original_main_stable", "frame": 3815})
        for index in range(len(stages)):
            with self.subTest(missing=index), self.assertRaises(ValueError):
                verify_named_original_play_after_recovery(
                    "\n".join(s for i, s in enumerate(stages) if i != index))
        # Reject anonymous timestamps, a mixed source epoch, and altered
        # source state even when all host-side confirmation markers remain.
        for bad in (
            good.replace("phase=main_menu frame=437", "phase=main_menu frame=440"),
            good.replace("phase=attract_title frame=940", "phase=attract_title frame=943"),
            good.replace("phase=demo_race frame=1529", "phase=demo_race frame=1532"),
            good.replace("source_revealed=1 frame=940", "source_revealed=1 frame=943"),
            good.replace("source_main_recovered=1 frame=3815", "source_main_recovered=1 frame=3818"),
            good.replace("frame=437 menu=d7", "frame=437 menu=84"),
            good.replace("frame=1529 menu=00 race=01", "frame=1529 menu=00 race=00"),
            good.replace("stock_entered players=1 menu=3c",
                         "stock_entered players=2 menu=3d"),
            good.replace("source_stable=60", "source_stable=1"),
            good.replace("stable=60", "stable=2"),
            good + "\nUR_BALDOSA_MODERN_ROOT active_profile_stale=1",
            good + "\nUR_BALDOSA_MODERN_ROOT stock_aborted=1",
            good + "\nUR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
        ):
            with self.subTest(bad=bad[-130:]), self.assertRaises(ValueError):
                verify_named_original_play_after_recovery(bad)

    def test_reject_forged_guest_events(self):
        good = "\n".join((OPEN, MAIN, TITLE, DEMO))
        bad = (
            good.replace(OPEN, ""),
            good.replace(TITLE + "\n", ""),
            good + "\n" + DEMO,
            "\n".join((OPEN, TITLE, MAIN, DEMO)),
            good.replace("frame=943", "frame=944"),
            good.replace("frame=1532", "frame=1531"),
            good.replace("menu=84", "menu=d7"),
            good.replace("race=01", "race=00"),
            good.replace("overlay_title=1", "overlay_title=0"),
        )
        for content in bad:
            with self.subTest(log=content[-95:]):
                with self.assertRaises(ValueError):
                    verify_original_source_attract(content)


if __name__ == "__main__":
    unittest.main()
