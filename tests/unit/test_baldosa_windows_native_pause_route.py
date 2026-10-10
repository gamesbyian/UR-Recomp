#!/usr/bin/env python3
"""Focus on source-derived Win32 guest CRC and pause-proof parser semantics."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_windows_native_pause_route as probe


class NativeWindowsPauseProbeTests(unittest.TestCase):
    def test_real_sdl_shared_root_requires_stock_menu_observation(self):
        baseline = (
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared\n"
            "UR_BALDOSA_MODERN_ROOT selected=1\n"
            "UR_BALDOSA_MODERN_ROOT selected=2\n"
            "UR_BALDOSA_MODERN_ROOT selected=3\n"
            "UR_BALDOSA_MODERN_ROOT route=3 unavailable=1\n"
            "UR_BALDOSA_MODERN_ROOT selected=2\n"
            "UR_BALDOSA_MODERN_ROOT selected=1\n"
            "UR_BALDOSA_MODERN_ROOT selected=0\n"
            "UR_BALDOSA_MODERN_ROOT stock_requested players=1\n"
            "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
        )
        self.assertIsNone(probe.verify_native_modern_root_log(baseline))
        for bad in (
            baseline.replace(" painted=1", " painted=0"),
            baseline.replace(" renderer=shared", " renderer=fake"),
            baseline.replace(" route=3 unavailable=1", " route=3 launched=1"),
            baseline.replace(" stock_entered players=1 menu=3c",
                             " stock_entered players=1 menu=d7"),
            baseline.replace(" stock_entered players=1 menu=3c",
                             " stock_entered players=2 menu=3d"),
            baseline.replace("opened=1", "opened=0"),
            baseline + baseline,
            baseline.replace("UR_BALDOSA_MODERN_ROOT selected=0\n", ""),
            baseline + "UR_BALDOSA_MODERN_ROOT stock_rejected=timeout\n",
        ):
            with self.subTest(bad=bad[-120:]):
                with self.assertRaisesRegex(ValueError, "Native"):
                    probe.verify_native_modern_root_log(bad)
        with self.assertRaisesRegex(ValueError, "out of order"):
            probe.verify_native_modern_root_log(
                baseline.replace(
                    "UR_BALDOSA_MODERN_ROOT route=3 unavailable=1\n",
                    "").replace(
                    "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n",
                    "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
                    "UR_BALDOSA_MODERN_ROOT route=3 unavailable=1\n"))
        two_player = (
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared\n"
            "UR_BALDOSA_MODERN_ROOT selected=1\n"
            "UR_BALDOSA_MODERN_ROOT selected=2\n"
            "UR_BALDOSA_MODERN_ROOT stock_requested players=2\n"
            "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n"
        )
        self.assertIsNone(probe.verify_native_modern_root_log(two_player, 2))
        with self.assertRaisesRegex(ValueError, "missing/duplicate"):
            probe.verify_native_modern_root_log(two_player, 1)
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            probe.verify_native_modern_root_log(two_player, 3)

    def test_reads_authoritative_framedump_crc_in_numeric_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for frame, value in ((10, "0xABCD"), (2, "0x00FF"), (1, "0x1234")):
                (root / f"frame_{frame:06}.json").write_text(
                    '{"crc32_wram": "' + value + '"}')
            self.assertEqual(probe.frame_crcs(root),
                             ["0x1234", "0x00ff", "0xabcd"])

    def test_missing_or_malformed_frame_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "No real"):
                probe.frame_crcs(root)
            (root / "frame_000001.json").write_text('{"bogus": "0xAA"}')
            with self.assertRaisesRegex(ValueError, "Missing real"):
                probe.frame_crcs(root)
            (root / "frame_000001.json").unlink()
            (root / "frame_invalid.json").write_text('{"crc32_wram": "0xAA"}')
            with self.assertRaisesRegex(ValueError, "Unexpected"):
                probe.frame_crcs(root)

    def test_pause_needs_all_three_real_witnesses(self):
        valid = ("UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1 modern_session=1 physical_sdl=1\n"
                 "UR_BALDOSA_NATIVE_PAUSE RELEASED guest=1952 frozen_pumps=24 physical_sdl=1\n"
                 "UR_BALDOSA_NATIVE_PAUSE RESUMED previous_guest=1952 new_guest=1953 frozen_pumps=24\n"
                 "UR_BALDOSA_NATIVE_RESTART SAME_FRAME guest=1900 sram_equal=1 wram_equal=1\n")
        self.assertEqual(set(probe.check_pause_log(valid)),
                         {"ARMED", "RELEASED", "RESUMED"})
        with self.assertRaisesRegex(ValueError, "live gameplay"):
            probe.check_pause_log(valid.replace("live_race=1", "live_race=0"))
        with self.assertRaisesRegex(ValueError, "Modern session API"):
            probe.check_pause_log(valid.replace("modern_session=1", "modern_session=0"))
        with self.assertRaisesRegex(ValueError, "physical SDL key edges"):
            probe.check_pause_log(valid.replace("physical_sdl=1", "physical_sdl=0"))
        with self.assertRaisesRegex(ValueError, "Native guest rollback"):
            probe.check_pause_log(valid.replace("wram_equal=1", "wram_equal=0"))
        with self.assertRaisesRegex(ValueError, "Native guest rollback"):
            probe.check_pause_log(valid.replace("sram_equal=1", "sram_equal=0"))
        with self.assertRaisesRegex(ValueError, "Missing"):
            probe.check_pause_log(valid.replace(" RESUMED ", " MISSING "))
        with self.assertRaisesRegex(ValueError, "too short"):
            probe.check_pause_log(valid.replace("frozen_pumps=24", "frozen_pumps=2"))
        with self.assertRaisesRegex(ValueError, "violation"):
            probe.check_pause_log(valid + "UR_BALDOSA_NATIVE_PAUSE FAIL=wrong\n")


    def test_delayed_restart_requires_real_elapsed_guest_frames(self):
        valid = (
            "UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1 modern_session=1 physical_sdl=1\n"
            "UR_BALDOSA_NATIVE_RESTART SAME_FRAME guest=1800 sram_equal=1 wram_equal=1\n"
            "UR_BALDOSA_NATIVE_RESTART DELAYED anchor_guest=1800 request_guest=1952 paused=1 sram_equal=1 wram_rewound=1\n"
            "UR_BALDOSA_NATIVE_PAUSE RELEASED guest=1952 frozen_pumps=24 physical_sdl=1\n"
            "UR_BALDOSA_NATIVE_PAUSE RESUMED previous_guest=1952 new_guest=1953 frozen_pumps=24\n"
        )
        self.assertEqual(
            probe.check_delayed_restart_log(valid, expected_request_frame=1952),
            {"anchor_guest": 1800, "request_guest": 1952},
        )
        for bad in (
            valid.replace("wram_rewound=1", "wram_rewound=0"),
            valid.replace("sram_equal=1 wram_rewound", "sram_equal=0 wram_rewound"),
            valid.replace("anchor_guest=1800", "anchor_guest=1949"),
            valid.replace("request_guest=1952 paused=1", "request_guest=1953 paused=1"),
            valid.replace(" paused=1 sram_equal=1 wram_rewound=1", " paused=0 sram_equal=1 wram_rewound=1"),
            valid.replace("UR_BALDOSA_NATIVE_RESTART DELAYED", "UR_BALDOSA_NATIVE_RESTART DUMMY"),
            valid + "UR_BALDOSA_NATIVE_RESTART DELAYED anchor_guest=1800 request_guest=1952 paused=1 sram_equal=1 wram_rewound=1\n",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    probe.check_delayed_restart_log(bad, expected_request_frame=1952)
        with self.assertRaisesRegex(ValueError, "violation"):
            probe.check_delayed_restart_log(
                valid + "UR_BALDOSA_NATIVE_PAUSE FAIL=bad_guest\n",
                expected_request_frame=1952)

    def test_second_native_process_reads_original_named_save_and_does_not_reseed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            user_root = (root / "with_named_profile" /
                         "Modern Player Data With Spaces")
            selected = user_root / "saves/profile-native-ci-rider"
            selected.mkdir(parents=True)
            before = bytes([17]) * 8192
            (selected / "save.srm").write_bytes(before)
            for name, folder in (
                ("host-profile.txt", selected),
                ("host-state-v1.txt", user_root),
                ("profiles-v1.txt", user_root),
            ):
                (folder / name).write_bytes(("preserve-" + name).encode())
            log = (
                "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
                "root=saves/profile-native-ci-rider\n"
                "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-rider "
                f"bytes=8192 fnv={probe.fnv32(before)}\n"
                "script f=2472 dump t480 ok\n"
                "script f=2472 quit\n"
            )
            def subprocess_fake(cmd, **kw):
                self.assertEqual(
                    kw["env"]["SNESRECOMP_USER_DATA_DIR"], str(user_root))
                self.assertEqual(
                    kw["env"]["UR_BALDOSA_MODERN_PROFILE_SELECT"], "1")
                self.assertNotIn("fixture", " ".join(cmd))
                # Native game legitimately updates SRAM on exit. The boot
                # hash must reflect PRE-RUN bytes, not the modified file.
                (selected / "save.srm").write_bytes(bytes([19]) * 8192)
                return subprocess.CompletedProcess(cmd, 0, log, "")
            with (
                mock.patch.object(probe.subprocess, "run",
                                  side_effect=subprocess_fake),
                mock.patch.object(probe, "frame_crcs",
                                  return_value=["0x1"] * 2472),
                mock.patch.object(probe, "verify_native_profile_checkpoint"),
            ):
                receipt = probe.run_existing_named_profile_fresh_process(
                    Path("real-baldosa.exe"), Path("retail.sfc"),
                    Path("2p-route.txt"), root, video="windows",
                    timeout=20, clean_frames=2473,
                    fixture=Path("native-typed-fixture.exe"))
            self.assertTrue(
                receipt["loaded_8192_byte_save_from_previous_process"])
            self.assertEqual(
                receipt["initial_native_sram_fnv32"], probe.fnv32(before))
            self.assertEqual(receipt["second_process_guest_frames"], 2472)
            self.assertFalse((user_root / "saves/save.srm").exists())
            self.assertEqual((selected / "save.srm").read_bytes(),
                             bytes([19]) * 8192)
            for name, folder in (
                ("host-profile.txt", selected),
                ("host-state-v1.txt", user_root),
                ("profiles-v1.txt", user_root),
            ):
                self.assertEqual(
                    (folder / name).read_bytes(), ("preserve-" + name).encode())

    def test_native_checkpoint_requires_acknowledgment_and_typed_readback(self):
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = Path("real-fixture.exe")
            ok = ("UR_BALDOSA_NATIVE_PROFILE CHECKPOINT "
                  "profile=native-ci-rider status=committed\n")
            expected = (
                "UR_BALDOSA_NATIVE_PROFILE VERIFIED "
                "profile=native-ci-rider sram=8192 generation=1\n")
            with mock.patch.object(probe.subprocess, "run",
                                   return_value=subprocess.CompletedProcess(
                                       [], 0, expected, "")) as execute:
                probe.verify_native_profile_checkpoint(
                    fixture, root, "native-ci-rider", ok, 20)
                self.assertEqual(
                    execute.call_args.args[0][-1], "--verify-native-save")
                for invalid in (
                    "", ok + ok,
                    ok.replace("committed", "profile_conflict"),
                    ok.replace("committed", "native_save_unverified"),
                    ok.replace("committed", "io_error"),
                ):
                    with self.assertRaisesRegex(ValueError, "acknowledged"):
                        probe.verify_native_profile_checkpoint(
                            fixture, root, "native-ci-rider", invalid, 20)
            with mock.patch.object(probe.subprocess, "run",
                                   return_value=subprocess.CompletedProcess(
                                       [], 46, "", "SRAM mismatch")):
                with self.assertRaisesRegex(ValueError, "diverged"):
                    probe.verify_native_profile_checkpoint(
                        fixture, root, "native-ci-rider", ok, 20)

    def test_second_named_modern_profile_admits_only_own_guest_sram(self):
        source = bytes(i % 251 for i in range(8192))
        second_hash = probe.fnv32(source)
        a_log = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
            "root=saves/profile-native-ci-rider\n"
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-rider "
            f"bytes=8192 fnv={second_hash}\n")
        b_log = a_log.replace("native-ci-rider", "native-ci-second")
        self.assertEqual(
            probe.verify_named_profile_boot_bytes(
                b_log, source, profile_id="native-ci-second"),
            {"bytes": 8192, "fnv32": second_hash})
        for corrupt in (
            a_log,
            b_log.replace("root=saves/profile-native-ci-second",
                          "root=saves/profile-native-ci-rider"),
            b_log.replace(second_hash, "00000000"),
            b_log + b_log,
        ):
            with self.subTest(corrupt=corrupt[:90]):
                with self.assertRaises(ValueError):
                    probe.verify_named_profile_boot_bytes(
                        corrupt, source, profile_id="native-ci-second")
        with self.assertRaisesRegex(ValueError, "Unknown named"):
            probe.verify_named_profile_boot_bytes(
                b_log, source, profile_id="../escape")

    def test_named_profile_terminal_must_reach_final_script_checkpoint(self):
        clean = 2473
        for frames in (2472, 2473):
            log = (f"script f={frames} dump t480 ok\n"
                   f"script f={frames} quit\n")
            self.assertEqual(
                probe.check_named_profile_guest_terminal(
                    ["0x1"] * frames, log, clean_frames=clean), frames)
            for corrupt in (
                log.replace("dump t480 ok", "dump t240 ok"),
                log.replace("quit", "wait"),
                log.replace(f"f={frames} quit", f"f={frames - 1} quit"),
            ):
                with self.subTest(frames=frames, corrupt=corrupt):
                    with self.assertRaisesRegex(ValueError, "terminal checkpoint"):
                        probe.check_named_profile_guest_terminal(
                            ["0x1"] * frames, corrupt, clean_frames=clean)
        for frames in (2471, 2474, 0):
            with self.subTest(frames=frames):
                with self.assertRaisesRegex(ValueError, "frame count"):
                    probe.check_named_profile_guest_terminal(
                        ["0x1"] * frames, "", clean_frames=clean)

    def test_real_named_modern_sram_boot_witness_is_unique_and_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            seed = Path(directory) / "real_native_guest_save.srm"
            data = bytes(i % 256 for i in range(8192))
            seed.write_bytes(data)
            fnv = probe.fnv32(data)
            self.assertEqual(len(fnv), 8)
            log = (
                "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
                "root=saves/profile-native-ci-rider\n"
                f"UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
                f"profile=native-ci-rider bytes=8192 fnv={fnv}\n"
            )
            self.assertEqual(
                probe.verify_named_profile_boot(log, seed),
                {"bytes": 8192, "fnv32": fnv})
            for bad in (
                log.replace(fnv, "ffffffff" if fnv != "ffffffff" else "00000000"),
                log.replace("BOOT_SRAM", "BOOT_WRONG"),
                log.replace("APPLIED", "REJECTED"),
                log.replace("profile=native-ci-rider", "profile=other-rider"),
                log + log,
            ):
                with self.subTest(log=bad[:80]):
                    with self.assertRaises(ValueError):
                        probe.verify_named_profile_boot(bad, seed)
            seed.write_bytes(data[:-1])
            with self.assertRaisesRegex(ValueError, "did not load"):
                probe.verify_named_profile_boot(log, seed)

    def test_host_frame_wram_detects_guest_rewind_even_when_guest_dump_names_repeat(self):
        def trace(offset_after_restart=0):
            result = []
            for frame in range(probe.HOST_TRACE_START, probe.HOST_TRACE_END + 1):
                rollback = frame > probe.HOST_RESTART_FRAME and offset_after_restart
                guest = frame - (34 if rollback else 0)
                fingerprint = ((frame + (offset_after_restart if rollback else 0)) * 41) & 0xffffffff
                result.append(
                    f"UR_BALDOSA_HOST_FRAME_CRC host={frame} guest={guest} "
                    f"hash={fingerprint:08x}"
                )
            return "\n".join(result) + "\n"

        baseline = trace()
        restarted = trace(7)
        receipt = probe.check_delayed_restart_host_trace(baseline, restarted)
        self.assertEqual(
            receipt["first_divergent_host_frame"],
            probe.HOST_RESTART_FRAME + 1)
        self.assertEqual(
            receipt["host_sample_count"],
            probe.HOST_TRACE_END - probe.HOST_TRACE_START + 1)
        self.assertLess(
            receipt["restarted_guest_counter_after_resume"],
            receipt["original_guest_counter_after_resume"])

        # Guest-indexed file CRCs may be overwritten by guest timeline rewind.
        # Identical file contents are NOT a negative control for host-relative
        # WRAM divergence. Only the real immutable host-frame stream is.
        with self.assertRaisesRegex(ValueError, "did not change"):
            probe.check_delayed_restart_host_trace(baseline, baseline)
        with self.assertRaisesRegex(ValueError, "before physical R"):
            bad = restarted.replace(
                f"host={probe.HOST_RESTART_FRAME} guest={probe.HOST_RESTART_FRAME}",
                f"host={probe.HOST_RESTART_FRAME} guest=1")
            probe.check_delayed_restart_host_trace(baseline, bad)
        with self.assertRaisesRegex(ValueError, "Missing/out-of-window"):
            probe.check_delayed_restart_host_trace(
                baseline, restarted.splitlines()[1:] and
                "\n".join(restarted.splitlines()[1:]) + "\n")
        with self.assertRaisesRegex(ValueError, "Duplicate host-frame"):
            line = restarted.splitlines()[0]
            probe.check_delayed_restart_host_trace(
                baseline, restarted + line + "\n")
        with self.assertRaisesRegex(ValueError, "Missing/out-of-window"):
            probe.check_delayed_restart_host_trace(baseline, "")


if __name__ == "__main__":
    unittest.main()
