#!/usr/bin/env python3
"""ROM-free negative witnesses for real no-args CMD native gamepad handoff."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from verify_baldosa_windows_extracted_launcher import (
    verify_first_user_cmd_relaunch_log,
)


def receipt() -> str:
    return (
        "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
        "profile=anonymous button=X\n"
        "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike "
        "activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT first_racer_created=1 "
        "activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
        "profile=anonymous button=A\n"
        "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
        "profile=anonymous button=B\n"
        "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
        "profile=anonymous button=B\n"
        "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
        "profile=anonymous button=A\n"
        "UR-BALDOSA-FIRST-RACER: Restarting with newly created racer.\n"
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
        "root=saves/profile-mike\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike "
        "bytes=8192 fnv=aaaaaaaa\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
        "profile=mike button=B\n"
        "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
        "profile=mike button=A\n"
    )


class NativeNoArgsGamepadRelaunchTest(unittest.TestCase):
    def test_good_two_process_source_receipt(self):
        verify_first_user_cmd_relaunch_log(receipt())

    def test_reject_absent_or_duplicate_semantic_button(self):
        good = receipt()
        first = "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
        for bad in (
            good.replace(first + "profile=anonymous button=X\n", ""),
            good.replace(first + "profile=mike button=A\n", ""),
            good.replace(first + "profile=anonymous button=X\n",
                         first + "profile=anonymous button=B\n"),
            good + first + "profile=mike button=A\n",
            good.replace("profile=mike button=B", "profile=anonymous button=B"),
            good.replace("profile=anonymous button=B\n",
                         "profile=anonymous button=A\n", 1),
            good.replace("UR-BALDOSA-FIRST-RACER: Restarting with newly created racer.",
                         "UR-BALDOSA-FIRST-RACER: Skipped restart."),
            good.replace("UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike",
                         "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew"),
            good.replace("UR_BALDOSA_MODERN_ROOT opened=1\n", "", 1),
        ):
            with self.subTest(tail=bad[-120:]), self.assertRaises(ValueError):
                verify_first_user_cmd_relaunch_log(bad)

    def test_no_args_route_is_real_p1_handler_not_new_script_or_result(self):
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        launcher = (ROOT / "tools/verify_baldosa_windows_extracted_launcher.py"
                    ).read_text()
        self.assertIn('std::strcmp(opt, "10") == 0', root)
        self.assertIn('ur_baldosa_modern_root_gamepad(0, button, 1)', root)
        self.assertIn("kGamepadBtn_X", root)
        self.assertIn("kGamepadBtn_B", root)
        self.assertIn("UR_BALDOSA_LAUNCHER_RESTART_SMOKE", root)
        self.assertIn('"UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "10"', launcher)
        self.assertIn("invoke_launcher(launcher, first_env, [], timeout)", launcher)
        self.assertNotIn("RtlWriteSram(", root)


if __name__ == "__main__":
    unittest.main()
