#!/usr/bin/env python3
"""Adversarial QA for one SDL P1 driving a genuine source-earned 1P race."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from run_baldosa_keyboard_pad_join_acceptance import (
    PAD_RACE, PAD_RACE_RETURN, verify_five_destination_pad_race,
    verify_five_destination_pad_post_result,
)

SOURCE = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(encoding="utf-8")
RUNNER = (ROOT / "tools/run_baldosa_keyboard_pad_join_acceptance.py").read_text(encoding="utf-8")

HOST = "[Gamepad] UR_CONTROLLER_SEAT assign instance=101 seat=0 reason=added"
PREFIX = [
    "UR_BALDOSA_MODERN_TITLE painted=1 raster=342x224 host=modern",
    "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=75 input_owned=1",
    "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared",
    "UR_BALDOSA_MODERN_ROOT selected=1",
    "UR_BALDOSA_MODERN_ROOT practice_opened=1 available=3 course=0 source_menu_required=1",
    "UR_BALDOSA_MODERN_DESTINATION stage=practice-picker raster=342x224 root=11,10,320,204 source=modern_product_view",
    "UR_BALDOSA_MODERN_ROOT practice_closed=1",
    "UR_BALDOSA_MODERN_ROOT selected=2",
    "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
    "UR_BALDOSA_MODERN_DESTINATION stage=multiplayer-join raster=342x224 root=11,10,320,204 source=modern_product_view",
    "UR_BALDOSA_MODERN_ROOT join_closed=1",
    "UR_BALDOSA_MODERN_ROOT selected=3",
    "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=0 unavailable=0",
    "UR_BALDOSA_MODERN_DESTINATION stage=records-1p raster=342x224 root=11,10,320,204 source=modern_product_view",
    "UR_BALDOSA_MODERN_ROOT records_closed=1",
    "UR_BALDOSA_MODERN_ROOT selected=4",
    "UR_BALDOSA_MODERN_ROOT options_opened row=DISPLAY display=WINDOWED vsync=ON volume=100 status=NONE help=0 load=missing",
    "UR_BALDOSA_MODERN_DESTINATION stage=options raster=342x224 root=11,10,320,204 source=modern_product_view",
    "UR_BALDOSA_MODERN_ROOT options_closed row=DISPLAY display=WINDOWED vsync=ON volume=100 status=NONE help=0 load=missing",
    "UR_BALDOSA_MODERN_ROOT selected=3",
    "UR_BALDOSA_MODERN_ROOT selected=2",
    "UR_BALDOSA_MODERN_ROOT selected=1",
    "UR_BALDOSA_MODERN_ROOT selected=0",
    "UR_BALDOSA_MODERN_ROOT stock_requested players=1",
    "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
]
TAIL = [
    "UR_BALDOSA_MODERN_PAD_RACE source_stock_setup=1 menu=3c",
    "UR_BALDOSA_MODERN_PAD_RACE source_start_pulses=4",
    "UR_BALDOSA_MODERN_PAD_RACE source_go=1 phase=8610 ticker=1",
    "UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p profile=mike course=course:01 source=guest",
    "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p race_host=100 result_host=200 finish_ticks60=1679 input_frames=500 input_runs=7 published=1",
]


class EarnedControllerJourney(unittest.TestCase):
    def test_source_uses_sdl_pad_and_never_scripts_guest_buttons(self):
        self.assertIn('std::strcmp(opt, "31") == 0', SOURCE)
        self.assertIn("SDL_GAMEPAD_BUTTON_START", SOURCE)
        self.assertIn("source_phase == 0x8610u", SOURCE)
        line = next(line for line in RUNNER.splitlines()
                    if line.startswith("PAD_RACE = "))
        self.assertIn("turbo on", line)
        self.assertIn("wait 7200", line)
        self.assertNotIn("press ", line)
        # The native script parser requires real line separators; a literal
        # backslash-n sequence fails before the SDL journey even starts.
        self.assertEqual(PAD_RACE.splitlines(), ["turbo on", "wait 7200", "quit"])
        self.assertEqual(PAD_RACE, "turbo on\nwait 7200\nquit\n")
        self.assertEqual(PAD_RACE_RETURN, "turbo on\nwait 11000\nquit\n")
        self.assertIn('std::strcmp(opt, "32") == 0', SOURCE)
        self.assertIn("reopened_frame + 900u", SOURCE)
        self.assertIn("reopened_frame + 1070u && !g_confirm_quit", SOURCE)
        self.assertIn("native_sdl_quit_queued=1", SOURCE)
        product_input = (ROOT / "tools/baldosa_native_product_execution.cpp").read_text(
            encoding="utf-8")
        self.assertIn("UR_BALDOSA_PRODUCT_INPUT_ISOLATION sample=", product_input)
        self.assertIn("g_host_owned_samples > 900u", product_input)
        self.assertIn("UR_BALDOSA_PRODUCT_INPUT_ISOLATION_DIAGNOSTICS", RUNNER)

    def test_real_source_earned_return_uses_non_acp_named_profile_root(self):
        # This is a source contract, not synthetic acceptance. The existing
        # same-PE Windows native journey actually creates two profiles in
        # separate processes, earns a source result, then reopens Records.
        self.assertIn('return_user = out / "user_earned_return_漢字-🚲"', RUNNER)
        self.assertIn('run_game(exe, rom, return_user, out / "return_create_p1"',
                      RUNNER)
        self.assertIn('run_game(exe, rom, return_user, out / "return_create_p2"',
                      RUNNER)
        self.assertIn('out / "five_destination_earned_return", "32"', RUNNER)
        self.assertIn('return_archive = return_user / "runs" / "mike"', RUNNER)
        self.assertIn('verify_five_destination_pad_post_result(return_log)',
                      RUNNER)
        self.assertIn('"earned_return_unicode_root":', RUNNER)
        # A fourth actual native process must cold-open the already earned
        # archive through the same five-destination Modern controller path.
        self.assertIn('out / "earned_return_cold_records", "29"', RUNNER)
        self.assertIn('verify_five_destination_pad_journey(cold_log)', RUNNER)
        self.assertIn('visible != [("1", "0")]', RUNNER)
        self.assertIn('cold_runs != return_after', RUNNER)
        self.assertIn('"earned_return_cold_records":', RUNNER)

    def test_earned_race_native_log_is_retained_for_independent_qa(self):
        # A summary receipt cannot independently establish the original
        # source milestones and uninterrupted SDL seat history. Keep the
        # exact native log alongside the same-PE acceptance receipt.
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text(encoding="utf-8")
        self.assertIn(
            "${{ runner.temp }}/ur-keyboard-pad-join/five_destination_earned_race/log.txt",
            workflow,
        )
        self.assertIn(
            "${{ runner.temp }}/ur-keyboard-pad-join/five_destination_earned_return/log.txt",
            workflow,
        )
        self.assertIn(
            "${{ runner.temp }}/ur-keyboard-pad-join/receipt.json",
            workflow,
        )

    def test_post_result_source_return_and_adversarial_cases(self):
        post = [
            "UR_BALDOSA_MODERN_PAD_RACE source_input_completed=1",
            "UR_BALDOSA_MODERN_PAD_POST source_observed frame=5500 menu=99 race=00 stage=0",
            "UR_BALDOSA_MODERN_PAD_POST result_continue_a=1 source_menu=99",
            "UR_BALDOSA_MODERN_PAD_POST track_back_x=1 source_menu=f6",
            "UR_BALDOSA_MODERN_PAD_POST tour_back_x=1 source_menu=6d",
            "UR_BALDOSA_MODERN_PAD_POST rider_back_x=1 source_menu=3c",
            "UR_BALDOSA_MODERN_PAD_POST root_back_b=1 source_menu=d7",
            "UR_BALDOSA_MODERN_ROOT reopened=1 menu=d7 guest_writes=0",
            "UR_BALDOSA_MODERN_PAD_POST reopened=1 source_menu=d7",
            "UR_BALDOSA_MODERN_ROOT reopened_painted=1 renderer=shared",
            "UR_BALDOSA_MODERN_PAD_POST idle_completed=1 frames=900 modern_visible=1",
            "UR_BALDOSA_MODERN_ROOT selected=1",
            "UR_BALDOSA_MODERN_ROOT selected=2",
            "UR_BALDOSA_MODERN_ROOT selected=3",
            "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=1 unavailable=0",
            "UR_BALDOSA_MODERN_DESTINATION stage=records-1p raster=342x224 root=11,10,320,204 source=modern_product_view",
            "UR_BALDOSA_MODERN_ROOT records_closed=1",
            "UR_BALDOSA_MODERN_PAD_POST quit_prompt_b=1",
            "UR_BALDOSA_MODERN_PAD_POST quit_confirm_a=1 prompt=1",
            "UR_BALDOSA_MODERN_ROOT quit_confirmed=1 native_sdl_quit_queued=1",
        ]
        isolation_idle = [
            f"UR_BALDOSA_PRODUCT_INPUT_ISOLATION sample={n} frame={6500+n} "
            "incoming=c0000000 guest=c0000000 queued=0000 host_owns=1"
            for n in (180, 360, 540, 720, 900)
        ]
        # The actual Windows SDL route consumes Modern pad presses before
        # the guest-word filter, so the seam sees presence bits, not button
        # bits. Samples 930/960 prove continued filtering after idle.
        isolation_press = [
            "UR_BALDOSA_PRODUCT_INPUT_ISOLATION sample=930 frame=7031 "
            "incoming=40000000 guest=40000000 queued=0000 host_owns=1",
            "UR_BALDOSA_PRODUCT_INPUT_ISOLATION sample=960 frame=7061 "
            "incoming=40000000 guest=40000000 queued=0000 host_owns=1",
        ]
        post_with_isolation = [
            *post[:10], *isolation_idle, post[10],
            *isolation_press, *post[11:],
        ]
        good = [HOST, *PREFIX, *TAIL, *post_with_isolation,
                "[host +30.064s] exit: SDL_QUIT event after 7176 frames\r"]
        verify_five_destination_pad_post_result("\n".join(good) + "\n")

        def move_result_observation(before_marker: str) -> list[str]:
            candidate = [line for line in good
                         if "PAD_POST source_observed frame=" not in line]
            index = next(i for i, line in enumerate(candidate)
                         if before_marker in line)
            candidate.insert(index, post[1])
            return candidate

        def move_before(moved: str, marker: str) -> list[str]:
            candidate = [line for line in good if line != moved]
            candidate.insert(candidate.index(marker), moved)
            return candidate

        mutants = {
            "result observed before race input completed":
                move_result_observation("source_input_completed=1"),
            "result observed after menu continuation":
                move_result_observation("track_back_x=1"),
            "duplicate original result observation": good + [post[1]],
            "missing result continue": [x for x in good if "result_continue_a=1" not in x],
            "missing track back": [x for x in good if "track_back_x=1" not in x],
            "missing tour back": [x for x in good if "tour_back_x=1" not in x],
            "missing rider back": [x for x in good if "rider_back_x=1" not in x],
            "no original MAIN": [x for x in good if "root_back_b=1" not in x],
            "missing idle witness": [x for x in good if "idle_completed=1" not in x],
            "idle after navigation": [x for x in good if "idle_completed=1" not in x] + [post[10]],
            "missing Quit prompt": [x for x in good if "quit_prompt_b=1" not in x],
            "missing Quit confirm": [x for x in good if "quit_confirm_a=1" not in x],
            "missing native SDL Quit": [x for x in good if "quit_confirmed=1" not in x],
            "rejected SDL Quit": good + ["UR_BALDOSA_MODERN_ROOT quit_event_rejected"],
            "missing native exit": [x for x in good if "exit: SDL_QUIT" not in x],
            "missing native input filter samples": [
                x for x in good if "PRODUCT_INPUT_ISOLATION" not in x
            ],
            "incomplete idle isolation": [
                x for x in good if "sample=720 " not in x
            ],
            "guest input leaked during Modern": [
                x.replace("sample=930 frame=7031 incoming=40000000 guest=40000000",
                          "sample=930 frame=7031 incoming=40000000 guest=40000100")
                for x in good
            ],
            "stock menu input queued under Modern": [
                x.replace("sample=930 frame=7031 incoming=40000000 guest=40000000 queued=0000",
                          "sample=930 frame=7031 incoming=40000000 guest=40000000 queued=0080")
                for x in good
            ],
            "missing post-idle native filter calls": [
                x for x in good if "sample=930 " not in x and "sample=960 " not in x
            ],
            "presence bit lost during navigation": [
                x.replace("sample=930 frame=7031 incoming=40000000 guest=40000000",
                          "sample=930 frame=7031 incoming=40000000 guest=00000000")
                for x in good
            ],
            "reordered post-idle samples": [
                *[x for x in good if "sample=930 " not in x],
                isolation_press[0],
            ],
            "script-only quit at fallback": [x.replace("after 7176 frames",
                                                    "after 11000 frames") for x in good],
            "duplicate native exit": good + ["[host +30.065s] exit: SDL_QUIT event after 7177 frames\r"],
            "zero-frame exit": [x.replace("after 7176 frames",
                                           "after 0 frames") for x in good],
            "Quit before Records close": move_before(
                post[-3], "UR_BALDOSA_MODERN_ROOT records_closed=1"),
            "spoofed unprefixed exit": [x.replace("[host +30.064s] ", "") for x in good],
            "duplicate source reentry": good + [
                "UR_BALDOSA_MODERN_ROOT reopened=1 menu=d7 guest_writes=0"
            ],
            "empty earned Records": [x.replace("validated=1", "validated=0") for x in good],
            "post-return controller replacement": good + [
                "[Gamepad] UR_CONTROLLER_SEAT assign instance=102 seat=0 reason=added"
            ],
            "no source result": [x for x in good if "NATIVE_RESULT" not in x],
            "unpainted navigation": [
                *[x for x in good if "reopened_painted=1" not in x],
                "UR_BALDOSA_MODERN_ROOT reopened_painted=1 renderer=shared",
            ],
        }
        for label, candidate in mutants.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                verify_five_destination_pad_post_result("\n".join(candidate) + "\n")

    def test_real_source_witness_and_adversarial_mutations(self):
        good = [HOST, *PREFIX, *TAIL]
        verify_five_destination_pad_race("\n".join(good) + "\n")
        mutants = {
            "missing native title paint": [x for x in good if "TITLE painted=1" not in x],
            "missing native root paint": [x for x in good if "ROOT painted=1" not in x],
            "title paint after root": [good[0], good[2], good[3],
                                       good[1], *good[4:]],
            "cropped Records": [
                x.replace("stage=records-1p raster=342x224 root=11,10,320,204",
                          "stage=records-1p raster=342x224 root=11,10,300,204")
                for x in good
            ],
            "wrong Options raster": [
                x.replace("stage=options raster=342x224",
                          "stage=options raster=256x224")
                for x in good
            ],
            "destination painter refusal": good + [
                "UR_BALDOSA_MODERN_DESTINATION paint_refused=1 stage=options"
            ],
            "no source GO": [x for x in good if "source_go=1" not in x],
            "no source result": [x for x in good if "NATIVE_RESULT" not in x],
            "no captured run": [x for x in good if "NATIVE_RUN CAPTURED" not in x],
            "unpublished": [x.replace("published=1", "published=0") for x in good],
            "GO before stock Start": good[:-4] + [good[-3], good[-4], *good[-2:]],
            "reassigned pad": good + ["[Gamepad] UR_CONTROLLER_SEAT assign instance=102 seat=0 reason=added"],
            "detached pad": good + ["[Gamepad] UR_CONTROLLER_SEAT vacate instance=101 seat=0 key=0001"],
            "duplicate result": good + [good[-1]],
            "foreign profile": [x.replace("profile=mike", "profile=andrew") for x in good],
            "wrong course": [x.replace("course=course:01", "course=course:02") for x in good],
        }
        for label, candidate in mutants.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                verify_five_destination_pad_race("\n".join(candidate) + "\n")


if __name__ == "__main__":
    unittest.main()
