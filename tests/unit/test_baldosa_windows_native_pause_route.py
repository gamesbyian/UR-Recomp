#!/usr/bin/env python3
"""Focus on source-derived Win32 guest CRC and pause-proof parser semantics."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_windows_native_pause_route as probe


class NativeWindowsPauseProbeTests(unittest.TestCase):
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
