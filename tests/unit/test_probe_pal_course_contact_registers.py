from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import probe_pal_course_contact_registers as tool


class PalCourseContactRegistersTests(unittest.TestCase):
    def test_only_read_exact_ldy_to_sty_transfer(self):
        src = bytes.fromhex("ac950e8c090f")
        row = tool.read_transfer(src, 0)
        self.assertEqual(row["source"], 0x0E95)
        self.assertEqual(row["destination"], 0x0F09)
        self.assertEqual(row["bytes"], "ac950e8c090f")
        self.assertIsNone(tool.read_transfer(b"\xad\x95\x0e\x8c\x09\x0f", 0))
        self.assertIsNone(tool.read_transfer(src[:5], 0))
        self.assertIsNone(tool.read_transfer(src, 1))

    def test_relocated_transfer_search_rejects_multiple_candidates(self):
        base = tool.cpu_to_offset(tool.P2_ENTRY_CPU)
        sample = bytearray(base + 300)
        pattern = bytes.fromhex("ac970e8c090f")
        sample[base - 9:base - 3] = pattern
        sample[base + 11:base + 17] = pattern
        row = tool.locate_transfer(
            sample, tool.P2_ENTRY_CPU, shift=0,
            source=0x0E97, destination=0x0F09, radius=16,
        )
        self.assertEqual(len(row["matches"]), 2)
        self.assertFalse(row["unambiguous"])
        other = tool.locate_transfer(
            sample, tool.P2_ENTRY_CPU, shift=-9,
            source=0x0E97, destination=0x0F09, radius=0,
        )
        self.assertEqual(len(other["matches"]), 1)
        self.assertTrue(other["unambiguous"])

    def test_prefix_homolog_shifts_are_independently_grounded(self):
        self.assertEqual(
            tool.independent_prefix_shift(tool.PROTO_ALIGN, "usa-retail"), 0
        )
        self.assertEqual(
            tool.independent_prefix_shift(tool.PROTO_ALIGN, "legacy-beta"), 0
        )
        self.assertEqual(
            tool.independent_prefix_shift(
                tool.PROTO_ALIGN, "pal-prototype-1994-11-29"
            ), -3,
        )
        self.assertEqual(
            tool.independent_prefix_shift(tool.EUROPE_ALIGN, "europe-retail"),
            19,
        )

    def test_rom_samples_report_their_actual_transfer_operands(self):
        if not all(p.is_file() for p in (
            tool.USA, tool.BETA, tool.PROTOTYPE, tool.EUROPE,
        )):
            self.skipTest("preserved original ROMs are required")
        report = tool.build_report()
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(len(report["builds"]), 4)
        by_build = {x["build"]: x for x in report["builds"]}
        for build in ("usa-retail", "legacy-beta"):
            row = by_build[build]
            self.assertEqual(row["candidate"]["p1_backing"], 0x0E95)
            self.assertEqual(row["candidate"]["p2_backing_candidate"], 0x0E97)
            self.assertEqual(row["candidate"]["shared_current_player"], 0x0F09)
            self.assertEqual(
                row["status"], "unique_structural_transfer_correspondence"
            )
        for build in ("pal-prototype-1994-11-29", "europe-retail"):
            with self.subTest(build=build):
                row = by_build[build]
                self.assertIsNotNone(row["candidate"])
                self.assertEqual(
                    row["p1_entry"]["bytes"][:2], "ac"
                )
                self.assertEqual(row["p1_entry"]["bytes"][6:8], "8c")
                self.assertTrue(0x0E00 <= row["candidate"]["p1_backing"] < 0x0F00)
                self.assertTrue(
                    0x0F00 <= row["candidate"]["shared_current_player"] < 0x1000
                )
        # Visible in the one-time PR unit-log evidence; preserves actual
        # regional operand discoveries without assuming USA addresses.
        print("PAL_COURSE_CONTACT_REGISTER_SCAN=" + json.dumps({
            key: {
                "status": row["status"],
                "candidate": row["candidate"],
                "p2_unique": row.get("p2_entry", {}).get("unambiguous"),
                "bank81_unique": {
                    n: v["unambiguous"]
                    for n, v in row.get("bank81_round_trips", {}).items()
                },
            }
            for key, row in by_build.items()
        }, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
