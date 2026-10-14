#!/usr/bin/env python3
"""No-ROM adversarial source contract, never physical controller acceptance."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_existing_profile_selector_qa as qa
from check_baldosa_win32_first_racer_evidence import SOURCE
from check_baldosa_win32_second_racer_go_qa import SECOND


def fixture():
    root = (
        "[Launcher] Config/saves anchored to "
        "'D:\\a\\_temp\\UR Baldosa Win32 Pause Route\\"
        "native_existing_p1_switch\\Switch Two Real Stock Racers'.\n"
    )
    common = (
        "[Gamepad] SDL reports 0 joystick(s). enable_gamepad=[1,1]\n"
        "[host +0.035s] SDL init ok: video=windows audio=dummy\n"
        "script f=0 turbo on\n"
    )
    first = root + common + "\n".join(SOURCE) + "\nscript f=900 quit\n"
    second = (
        root + common + SECOND[0] + "\n" + SECOND[1] +
        "\nUR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=d4dc382b\n" +
        "\n".join(SECOND[2:]) + "\nscript f=900 quit\n"
    )
    def switch(profile, to, fnv):
        return (
            root + common +
            f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile} root=saves/profile-{profile}\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            f"UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile={profile} bytes=8192 fnv={fnv}\n"
            f"UR_BALDOSA_MODERN_ROOT existing_p1_opened=1 from={profile} to={to} activation=next_process\n"
            f"UR_BALDOSA_NATIVE_P1_SWITCH status=0 from={profile} to={to} activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT existing_p1_saved=1 activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT existing_p1_closed=1\n"
            "UR_BALDOSA_MODERN_ROOT existing_p1_stale_race_blocked=1\n"
            "script f=900 quit\n"
            "UR_BALDOSA_NATIVE_PROFILE PREFLIGHT_REJECTED status=3\n"
            "UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed\n"
        )
    third = switch("mike", "andrew", "2adcbf8d")
    fourth = switch("andrew", "mike", "999f4aae")
    last = (
        root + common +
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=2adcbf8d\n"
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=0 unavailable=0\n"
        "UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=0 unavailable=0 selected=0\n"
        "UR_BALDOSA_MODERN_ROOT records_closed=1\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
        "script f=1800 quit\n"
    )
    report = {
        "scope": "native-p1-existing-profile-selector-real-controller-root-next-boot",
        "canonical_catalog_sha256": "f42bf482f9cce61317fdf1d9c238fbdde65a5bd740466e95d40a48037a4fd131",
        "controller_root_p1_switches": ["mike->andrew", "andrew->mike"],
        "created_in_actual_frontend": ["mike", "andrew"],
        "fresh_native_boot_restored_mike": True,
        "paired_guest_result_accepted_by_this_probe": False,
        "physical_gamepad_hardware_accepted": False,
        "release_gate_credit": 0,
        "source_guest_hot_swap": False,
    }
    return report, first, second, third, fourth, last


class Win32ExistingProfileSelectorIndependent(unittest.TestCase):
    def check(self, values):
        return qa.audit(json.dumps(values[0]).encode(), *(x.encode() for x in values[1:]))

    def test_five_synthetic_processes_have_narrow_hosted_only_scope(self):
        result = self.check(fixture())
        self.assertTrue(result["p1_source_switch_mike_to_andrew_then_back_to_mike_observed"])
        self.assertFalse(result["newly_earned_source_scored_2p_result_accepted"])
        self.assertFalse(result["saved_catalog_selector_or_SRAM_bytes_independently_decoded"])
        self.assertFalse(result["physical_two_gamepads_or_audio_accepted"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_win32_crlf_and_real_stale_guest_preflight_disposition(self):
        data = fixture()
        self.assertTrue(self.check([data[0], *(x.replace("\n","\r\n") for x in data[1:])])[
            "source_confirmed_stale_race_block_for_both_switches"])

    def test_report_false_hardware_and_results_claims_are_rejected(self):
        data = fixture()
        for key, val in (
            ("scope", "full-release"),
            ("controller_root_p1_switches", ["mike->andrew"]),
            ("created_in_actual_frontend", ["mike"]),
            ("fresh_native_boot_restored_mike", False),
            ("paired_guest_result_accepted_by_this_probe", True),
            ("physical_gamepad_hardware_accepted", True),
            ("source_guest_hot_swap", True),
            ("release_gate_credit", True),
            ("release_gate_credit", 1),
            ("canonical_catalog_sha256", "bad"),
        ):
            bad = copy.deepcopy(list(data))
            bad[0][key] = val
            with self.subTest(field=key):
                with self.assertRaises(ValueError):
                    self.check(bad)
        bad = copy.deepcopy(list(data))
        bad[0]["full_release_accepted"] = True
        with self.assertRaises(ValueError):
            self.check(bad)

    def test_race_after_switch_or_wrong_profile_or_late_preflight_fails(self):
        data = fixture()
        cases = (
            (2, "existing_p1_opened=1", "existing_p1_opened=0"),
            (2, "status=0 from=mike", "status=0 from=andrew"),
            (2, "existing_p1_stale_race_blocked=1", "existing_p1_stale_race_blocked=0"),
            (2, "native_save_preflight_failed", "native_save_preflight_ok"),
            (2, "script f=900 quit", "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\nscript f=900 quit"),
            (3, "profile=andrew bytes=8192", "profile=mike bytes=8192"),
            (3, "existing_p1_saved=1", "existing_p1_saved=0"),
            (4, "fnv=2adcbf8d", "fnv=00000000"),
            (4, "paired=0 unavailable=0", "paired=1 unavailable=0"),
            (4, "stock_entered players=1 menu=3c", "stock_entered players=2 menu=3d"),
            (1, "preset=1 id=andrew", "preset=2 id=martin"),
        )
        for index, before, after in cases:
            bad = list(data)
            self.assertIn(before,bad[index+1])
            bad[index+1] = bad[index+1].replace(before,after)
            with self.subTest(index=index,token=before):
                with self.assertRaises(ValueError):
                    self.check(bad)

    def test_shadowed_switch_receipts_and_cross_root_false_positive_fail(self):
        base = fixture()
        for process, before, after in (
            (2, "Switch Two Real Stock Racers",
             "Different User Root"),
            (3, "existing_p1_stale_race_blocked=1",
             "existing_p1_stale_race_blocked=0"),
            (4, "profile=mike bytes=8192",
             "profile=andrew bytes=8192"),
        ):
            bad = list(base)
            bad[process + 1] = bad[process + 1].replace(before, after)
            with self.subTest(process=process, changed=before):
                with self.assertRaises(ValueError):
                    self.check(bad)
        shadow = list(base)
        shadow[3] += (
            "not-a-native-source-event: UR_BALDOSA_NATIVE_P1_SWITCH "
            "status=0 from=mike to=andrew activation=next_process\n"
        )
        with self.assertRaises(ValueError):
            self.check(shadow)

    def test_zip_consumer_requires_every_native_process(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.zip"
            def write(n):
                with zipfile.ZipFile(path, "w") as z:
                    for name,value in zip(qa.FILES[:n], [json.dumps(data[0]),*data[1:]][:n]):
                        z.writestr(qa.PREFIX + name, value)
            write(6)
            self.assertEqual(len(qa.read_archive(path)),6)
            write(5)
            with self.assertRaises(ValueError):
                qa.read_archive(path)


if __name__ == "__main__":
    unittest.main()
