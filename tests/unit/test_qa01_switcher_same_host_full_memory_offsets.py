"""Original/Baldosa Switcher read-only guest full-memory offset diagnostic guardrails."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as target


class SwitcherFullMemory5782OffsetsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ref, self.native = (Path(self.tmp.name) / name
                                 for name in ("ref", "native"))
        self.ref.mkdir()
        self.native.mkdir()
        self.same_host = {
            "schema": "UR-QA01-SWITCHER-PENULTIMATE-SAME-HOST/1",
            "original_absolute_host": 5782,
            "native_absolute_host": 5782,
            "result_absolute_host": 5783,
            "reference_guest_relative_frame": 4703,
            "native_guest_relative_frame": 4701,
        }

    def paths(self, kind):
        return (
            self.ref / f"source-host-minus-one.{kind}.bin",
            self.native / f"scene-04701.{kind}.bin",
        )

    def populate(self):
        for kind, size in target.BOWL_TALLY_MEMORY_SIZES.items():
            a, b = self.paths(kind)
            a.write_bytes(bytes(size))
            b.write_bytes(bytes(size))

    def capture(self, witness=None):
        return target.observe_switcher_same_host_memory_offsets(
            self.ref, self.native, self.same_host if witness is None else witness)

    def test_genuine_three_class_complete_identical_memory_is_still_nonadmission(self):
        self.populate()
        v = self.capture()
        self.assertEqual(v["schema"], "UR-QA01-SWITCHER-5782-FULL-GUEST-OFFSETS/1")
        self.assertEqual(v["original_host_frame"], 5782)
        self.assertEqual(v["native_host_frame"], 5782)
        self.assertTrue(v["all_197120_guest_bytes_equal"])
        self.assertEqual(sum(x["observed_guest_bytes_per_engine"]
                             for x in v["memory_classes"].values()), 197120)
        for kind, values in v["memory_classes"].items():
            self.assertTrue(values["exact_byte_match"], kind)
            self.assertEqual(values["different_byte_count"], 0)
            self.assertFalse(values["offsets_truncated"])
            self.assertEqual(values["different_byte_offsets"], [])
        self.assertFalse(v["original_movie_input_modified"])
        self.assertEqual(v["release_complete_event_credit"], 0)
        self.assertIn("cannot prove", v["limitation"])

    def test_complete_byte_differences_capture_offsets_only_not_guest_bytes(self):
        self.populate()
        for kind, addresses in (("wram", (0, 0x00CE, 0x119D)),
                                ("vram", (0x120, 0xFFF)),
                                ("cgram", (511,))):
            a, b = self.paths(kind)
            data = bytearray(b.read_bytes())
            for index in addresses:
                data[index] = 0xA7
            b.write_bytes(data)
        v = self.capture()
        self.assertFalse(v["all_197120_guest_bytes_equal"])
        self.assertEqual(v["memory_classes"]["wram"]["different_byte_count"], 3)
        self.assertEqual(v["memory_classes"]["wram"]["different_byte_offsets"],
                         ["0x00000", "0x000CE", "0x0119D"])
        self.assertEqual(v["memory_classes"]["vram"]["different_byte_offsets"],
                         ["0x00120", "0x00FFF"])
        self.assertEqual(v["memory_classes"]["cgram"]["different_byte_offsets"],
                         ["0x001FF"])
        self.assertNotIn("167", json.dumps(v))
        self.assertNotIn("0xA7", json.dumps(v))
        self.assertEqual(v["release_complete_event_credit"], 0)

    def test_address_reporting_is_bounded_but_full_difference_count_is_preserved(self):
        self.populate()
        a, b = self.paths("wram")
        data = bytearray(b.read_bytes())
        for i in range(180):
            data[i] = 1
        b.write_bytes(data)
        v = self.capture()
        self.assertEqual(v["memory_classes"]["wram"]["different_byte_count"], 180)
        self.assertEqual(len(v["memory_classes"]["wram"]["different_byte_offsets"]), 128)
        self.assertTrue(v["memory_classes"]["wram"]["offsets_truncated"])
        self.assertFalse(v["all_197120_guest_bytes_equal"])

    def test_missing_partial_wrong_case_or_wrong_host_witness_fails_closed(self):
        for fields in ({"schema": "invented"},
                       {"original_absolute_host": 5781},
                       {"native_absolute_host": 5783},
                       {"result_absolute_host": 5784},
                       {"reference_guest_relative_frame": 4701},
                       {"native_guest_relative_frame": 4703}):
            with self.subTest(fields=fields):
                with self.assertRaisesRegex(target.CompleteEventError, "attested"):
                    self.capture(dict(self.same_host, **fields))
        with self.assertRaisesRegex(target.CompleteEventError, "missing"):
            self.capture()
        self.populate()
        ref, native = self.paths("wram")
        ref.write_bytes(b"short")
        with self.assertRaisesRegex(target.CompleteEventError, "size"):
            self.capture()
        ref.write_bytes(bytes(0x20000))
        native.unlink()
        with self.assertRaisesRegex(target.CompleteEventError, "missing"):
            self.capture()
        native.write_bytes(bytes(0x20000))
        self.paths("vram")[1].write_bytes(bytes(0xFFFF))
        with self.assertRaisesRegex(target.CompleteEventError, "size"):
            self.capture()


if __name__ == "__main__":
    unittest.main()
