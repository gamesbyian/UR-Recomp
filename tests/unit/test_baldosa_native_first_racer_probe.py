#!/usr/bin/env python3
"""Strict first anonymous process and second real named process log admission."""
import sys
from pathlib import Path
import unittest
import subprocess
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_native_first_racer_probe as probe


class FirstNativeRacerLogTests(unittest.TestCase):

    def test_real_native_subprocess_utf8_path_is_not_decoded_as_windows_acp(self):
        # Run a real UTF-8-emitting child while intercepting the executable
        # name only. The production run_game() still owns subprocess decoding
        # and writing the retained log; this works on POSIX and Win32 Python.
        raw_path = "user_earned_return_漢字-🚲"
        program = (
            "import sys; "
            "sys.stdout.buffer.write('UR_NATIVE path=" + raw_path +
            "\\n'.encode('utf-8')); "
            "sys.stderr.buffer.write('UR_NATIVE second=" + raw_path +
            "\\n'.encode('utf-8'))"
        )
        real_run = subprocess.run
        def child(_arguments, **kwargs):
            return real_run([sys.executable, "-c", program], **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(probe.subprocess, "run", side_effect=child) as invoked:
                log = probe.run_game(
                    root / "host.exe", root / "original.sfc",
                    root / raw_path, root / "work",
                    "4", "turbo on\\nwait 1\\nquit\\n", "dummy", 15)
                self.assertEqual(invoked.call_args.kwargs["encoding"], "utf-8")
                self.assertEqual(invoked.call_args.kwargs["errors"], "replace")
            self.assertEqual(log.count(raw_path), 2)
            self.assertNotIn("\\ufffd", log)
            self.assertEqual((root / "work" / "log.txt").read_text(encoding="utf-8"), log)

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

    def test_nondefault_racer_requires_actual_menu_navigation_and_full_sram(self):
        sample = (
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_preset=1\n"
            "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=1 id=andrew "
            "activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process\n"
        )
        probe.verify_creation(sample, preset=1)
        for bad in (
            sample.replace("first_racer_preset=1", "first_racer_preset=0"),
            sample.replace("preset=1 id=andrew", "preset=0 id=mike"),
            sample.replace("id=andrew", "id=mike"),
            sample + sample,
            sample + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
        ):
            with self.subTest(bad=bad[-100:]):
                with self.assertRaises(ValueError):
                    probe.verify_creation(bad, preset=1)
        with self.assertRaises(ValueError):
            probe.verify_creation(sample, preset=2)

        raw = bytes(range(256)) * 32
        boot = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew "
            "root=saves/profile-andrew\n"
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=andrew "
            f"bytes=8192 fnv={probe.fnv32(raw)}\n"
        )
        probe.verify_boot_sram(boot, raw, profile="andrew")
        with self.assertRaises(ValueError):
            probe.verify_boot_sram(boot, raw, profile="mike")
        with self.assertRaises(ValueError):
            probe.verify_boot_sram(boot.replace(probe.fnv32(raw), "deadbeef"),
                                   raw, profile="andrew")
        with self.assertRaises(ValueError):
            probe.verify_boot_sram(boot + boot, raw, profile="andrew")
        source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(
            encoding="utf-8")
        self.assertIn("UR_BALDOSA_FIRST_RACER_TEST_PRESET", source)
        self.assertIn("second_stock_preset && frame == 61", source)

    def test_exact_first_racer_sram_boot_line_and_hash(self):
        # Real native trace line delimiters are actual newlines.
        stock = bytes(range(256)) * 32
        good = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
            "root=saves/profile-mike\n"
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike "
            f"bytes=8192 fnv={probe.fnv32(stock)}\n"
        )
        probe.verify_boot_sram(good, stock)
        for bad in (
            good.replace("profile-mike", "profile-another"),
            good.replace(probe.fnv32(stock), "deadbeef"),
            good + good,
            good.replace("bytes=8192", "bytes=8191"),
            good.replace("APPLIED profile=mike", "APPLIED profile=other"),
        ):
            with self.subTest(bad=bad[-110:]):
                with self.assertRaises(ValueError):
                    probe.verify_boot_sram(bad, stock)

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
