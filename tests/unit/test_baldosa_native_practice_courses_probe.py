#!/usr/bin/env python3
"""Practice-breadth probe: seed, case table and log verifier are strict."""
from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "native"))
import baldosa_native_practice_courses_probe as probe


def good_log(track: int, name: str, available: int) -> str:
    return (
        f"UR_BALDOSA_MODERN_ROOT practice_opened=1 available={available} "
        "course=0 source_menu_required=1\n"
        "UR_BALDOSA_MODERN_ROOT practice_sram_sandbox=1 bytes=8192 "
        "root=practice-session publication=disabled\n"
        f"UR_BALDOSA_MODERN_ROOT practice_requested=1 course={track} "
        f"name={name} source_route=stock\n"
        f"UR_BALDOSA_MODERN_ROOT practice_entered=1 course={track} "
        f"original_course={track + 1} race=1 source_identity=verified\n"
        "UR_BALDOSA_MODERN_ROOT practice_sram_restored=1 bytes=8192 "
        "original_root=1\n")


class PracticeCoursesProbeTests(unittest.TestCase):
    def test_tier2_seed_is_formatted_valid_and_hunter_free(self):
        data = probe.tier2_seed()
        self.assertEqual(len(data), 8192)
        self.assertEqual(data[:12], b"ASJIver3.30\xff")
        self.assertEqual(data[0x748], 0)
        self.assertTrue(all(data[0x10D3 + i] == 2 for i in range(16)))
        self.assertTrue(all(data[0x10FD + i] == 2 for i in range(16)))
        words = struct.unpack_from("<170H", data, 0x5E8)
        self.assertEqual(struct.unpack_from("<H", data, 0x73C)[0],
                         sum(words) & 0xFFFF)

    def test_case_tables_walk_only_courses_the_stock_menu_offers(self):
        tier0 = [t for _, _, t, _ in probe.TIER0]
        tier2 = [t for _, _, t, _ in probe.TIER2]
        self.assertTrue(all((t // 5) in (0, 2, 4, 6) for t in tier0))
        self.assertTrue(all(t < 40 for t in tier2))  # Hunter never offered
        # picker ordinal (steps) equals the position among unlocked courses
        open0 = [t for t in range(45) if (t // 5) in (0, 2, 4, 6)]
        for _, steps, track, _ in probe.TIER0:
            self.assertEqual(open0[steps], track)
        for _, steps, track, _ in probe.TIER2:
            self.assertEqual(steps, track)

    def test_verifier_rejects_missing_wrong_and_bypassed_stages(self):
        probe.verify_case(good_log(10, "LOOPER", 20), 10, "LOOPER", 20)
        with self.assertRaises(ValueError):
            probe.verify_case(good_log(10, "LOOPER", 20), 10, "LOOPER", 40)
        with self.assertRaises(ValueError):
            probe.verify_case(good_log(10, "LOOPER", 20), 11, "MEGAJUMP", 20)
        with self.assertRaises(ValueError):
            probe.verify_case(
                good_log(10, "LOOPER", 20)
                + "UR_BALDOSA_MODERN_ROOT practice_rejected=timeout\n",
                10, "LOOPER", 20)
        with self.assertRaises(ValueError):
            probe.verify_case(
                good_log(10, "LOOPER", 20).replace(
                    "practice_sram_restored=1", "x"), 10, "LOOPER", 20)

    def test_restart_in_practice_verifier_is_strict(self):
        good = (
            "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=0 "
            "original_course=1 race=1 source_identity=verified\n"
            "UR_BALDOSA_NATIVE_PAUSE ARMED guest=2500 live_race=1 "
            "modern_session=1 physical_sdl=1\n"
            "UR_BALDOSA_NATIVE_RESTART DELAYED anchor_guest=973 "
            "request_guest=2500 paused=1 sram_equal=1 wram_rewound=1\n"
            "UR_BALDOSA_NATIVE_PAUSE RESUMED previous_guest=2500 new_guest=2501 "
            "frozen_pumps=24\n"
            "UR_BALDOSA_MODERN_ROOT practice_sram_restored=1 bytes=8192 "
            "original_root=1\n")
        probe.verify_restart(good)
        for bad in (good.replace("sram_equal=1", "sram_equal=0"),
                    good.replace("wram_rewound=1", "wram_rewound=0"),
                    good.replace("anchor_guest=973", "anchor_guest=2600"),
                    good.replace("RESUMED", "STUCK"),
                    good.replace("practice_sram_restored=1", "x"),
                    good + good):
            with self.assertRaises(ValueError):
                probe.verify_restart(bad)

    def test_claims_no_hardware_or_release_credit(self):
        text = Path(probe.__file__).read_text()
        self.assertIn('"physical_gamepad_certified": False', text)
        self.assertIn('"release_gate_credit": 0', text)
        self.assertIn('"hunter_admitted": False', text)


if __name__ == "__main__":
    unittest.main()
