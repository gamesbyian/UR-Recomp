"""Read-only post-result SRAM address attribution: synthetic contract checks."""
from __future__ import annotations

import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_postresult_sram_diff as m


class ZooSramByteAttributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ref = self.root / "ref"
        self.native = self.root / "native"
        self.ref.mkdir()
        self.native.mkdir()
        self.report = self.fixture()

    def fixture(self):
        r = {
            "schema_version": 1, "name": "zoom-zoo", "course_id": "course:02",
            "native_backend": "pinned-baldosa",
            "rom_sha256": "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
            "original_movie_sha256": "a" * 64,
            "source_sram_sha256": "b" * 64,
            "original_movie_window_sha256": "c" * 64,
            "reference_core_sha256": "d" * 64,
            "native_executable_sha256": "e" * 64,
            "input_sha256": "f" * 64,
            "reference_entry": 1017, "native_entry": 1019,
            "original_source_event": {"original_entry_frame": 3190,
                                      "original_result_frame": 8353},
            "comparison": {"terminal_result_frame_matched": True,
                           "terminal_result_guest_frame": {
                               "reference_relative": 5163, "native_relative": 5163}},
            "source_terminal_followthrough": {
                "schema": "UR-QA01-SOURCE-ORIGINAL-NATIVE-RESULT-FOLLOWTHROUGH/2",
                "battery_sram_snapshot_bytes_per_guest": 8192,
                "battery_sram_cold_process_persistence_proven": False,
                "release_complete_usa_event_credit": 0,
                "all_followthrough_full_sram_pairs_equal": False,
                "samples": [],
            },
        }
        for at in m.OFFSETS:
            ref = bytearray(m.SIZE)
            nat = bytearray(ref)
            if at >= 64:
                nat[0x0424] = 1
                nat[0x0551] = 7
                nat[0x0600] = 3
            for side, directory, raw in (("original", self.ref, ref),
                                          ("native", self.native, nat)):
                (directory / f"original-follow-{at:02d}.sram.bin").write_bytes(raw)
            records = {side: m.ranked_record_receipt(raw, 1)
                       for side, raw in (("original", ref), ("native", nat))}
            r["source_terminal_followthrough"]["samples"].append({
                "offset_from_each_observed_result_onset": at,
                "independently_observed_replay_host_frames": {
                    "original": 1017 + 5163 + at, "native": 1019 + 5163 + at},
                "source_original_movie": {"original_movie_host_frame": 8353 + at},
                "fresh_guest_battery_sram": {
                    side: {"full_sram_bytes": 8192,
                           "crawler_course_track_index": 1,
                           "in_memory_snapshot_only": True,
                           "cold_process_reload_proven": False,
                           "sram_sha256": hashlib.sha256(raw).hexdigest(),
                           "crawler_record_three_ranks": records[side][0],
                           "record_table_checksum_stored": records[side][1],
                           "record_table_checksum_calculated": records[side][2],
                           "record_table_checksum_matches_at_sample": (
                               records[side][1] == records[side][2])}
                    for side, raw in (("original", ref), ("native", nat))},
                "sram_full_bytes_equal": ref == nat,
                "sram_course_three_rank_records_equal": records["original"][0] == records["native"][0],
            })
        return r

    def test_source_qualified_byte_regions_and_sample_interval(self):
        result = m.analyze(self.report, self.ref, self.native)
        self.assertEqual(result["first_sampled_full_sram_difference_offset"], 64)
        self.assertTrue(result["preceding_sampled_pair_equal"])
        self.assertEqual(result["release_complete_usa_event_credit"], 0)
        self.assertFalse(result["first_execution_time_of_difference_known"])
        self.assertFalse(result["cold_process_persistence_proven"])
        delta = result["observations"][4]["paired"]
        self.assertEqual(delta["differing_byte_count"], 3)
        self.assertEqual(delta["first_differing_address"], "0x0424")
        self.assertEqual(delta["regions"]["track_record_words"], 1)
        self.assertEqual(delta["regions"]["track_record_holders"], 1)
        self.assertEqual(delta["regions"]["other_battery_sram"], 1)
        self.assertEqual(result["observations"][4][
            "relative_to_previous_observation"]["native_changed_bytes"], 3)

    def test_full_sram_reads_are_hash_bound_and_missingness_fails_closed(self):
        row = self.native / "original-follow-64.sram.bin"
        raw = bytearray(row.read_bytes())
        raw[0x0550] ^= 1
        row.write_bytes(raw)
        with self.assertRaisesRegex(m.EvidenceError, "SHA256"):
            m.analyze(self.report, self.ref, self.native)
        row.unlink()
        with self.assertRaisesRegex(m.EvidenceError, "missing raw SRAM"):
            m.analyze(self.report, self.ref, self.native)

    def test_does_not_normalize_frame_offsets_or_release_gates(self):
        for mutation in (
            lambda p: p["comparison"]["terminal_result_guest_frame"].__setitem__("native_relative", 5162),
            lambda p: p["source_terminal_followthrough"]["samples"][4]["independently_observed_replay_host_frames"].__setitem__("native", 9999),
            lambda p: p["source_terminal_followthrough"].__setitem__("release_complete_usa_event_credit", 1),
            lambda p: p["source_terminal_followthrough"]["samples"].pop(),
        ):
            r = copy.deepcopy(self.report)
            mutation(r)
            with self.subTest(mutation=mutation), self.assertRaises(m.EvidenceError):
                m.analyze(r, self.ref, self.native)

    def test_limited_address_samples_and_all_address_digest(self):
        a = bytes(m.SIZE)
        b = bytearray(a)
        for n in range(120):
            b[0x0600 + n] = 1
        result = m.delta(a, b)
        self.assertEqual(result["differing_byte_count"], 120)
        self.assertFalse(result["address_list_complete"])
        self.assertEqual(len(result["first_differences"]), m.SHOW_LIMIT)
        self.assertNotEqual(result["all_difference_addresses_sha256"], "")
        with self.assertRaises(m.EvidenceError):
            m.delta(a[:-1], b)


if __name__ == "__main__":
    unittest.main()
