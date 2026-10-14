#!/usr/bin/env python3
"""Strict first anonymous process and second real named process log admission."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_native_first_racer_probe as probe


class FirstNativeRacerLogTests(unittest.TestCase):
    def test_creation_requires_canonical_next_boot_not_live_guest_hot_swap(self):
        valid = (
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process\n"
            "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike "
            "activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process\n"
        )
        probe.verify_creation(valid)
        for bad in (
            valid.replace("status=0", "status=1"),
            valid + valid,
            valid + "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n",
            valid + "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike\n",
            valid.replace("activation=next_process", "activation=live"),
        ):
            with self.subTest(bad=bad[-120:]):
                with self.assertRaises(ValueError):
                    probe.verify_creation(bad)

    def test_reboot_requires_real_selected_native_sram_and_stock_handoff(self):
        valid = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike "
            "bytes=8192 fnv=12345678\n"
            "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
        )
        probe.verify_reboot(valid)
        for bad in (
            valid.replace("profile=mike ", "profile=other ", 1),
            valid.replace("bytes=8192", "bytes=4096"),
            valid + valid,
            valid + "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n",
            valid + "UR_BALDOSA_MODERN_ROOT first_racer_created=1\n",
        ):
            with self.subTest(bad=bad[-120:]):
                with self.assertRaises(ValueError):
                    probe.verify_reboot(bad)


if __name__ == "__main__":
    unittest.main()
