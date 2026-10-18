"""ROM-free negative tests for source-original Bowl WRAM/SRAM three-way archive."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_bowl_movie_sram_crosswalk as census


def fixture(folder: Path):
    report = {
        "name": "bowl", "course_id": "course:03",
        "native_backend": "pinned-baldosa",
        "reference_entry": 984, "native_entry": 985,
        "comparison": {"terminal_result_guest_frame":
                       {"reference_relative": 3365, "native_relative": 3364}},
        "original_source_event":
            {"original_entry_frame": 8620, "original_result_frame": 11985},
        "original_movie_sha256": "a"*64,
        "native_executable_sha256": "b"*64,
        "bowl_source_movie_three_guest_memory": {
            "sample_offsets": list(census.OFFSETS), "sample_count": 8,
            "release_complete_event_credit": 0,
            "original_movie_controller_masks_modified": False,
            "samples": []},
    }
    members = {}
    observations = report["bowl_source_movie_three_guest_memory"]["samples"]
    for offset in census.OFFSETS:
        row = {
            "offset_from_source_movie_bowl_result": offset,
            "movie_absolute_host_frame": 11985 + offset,
            "movie_original": {}, "fresh_guests": {}}
        captured = {}
        for side, prefix in (
            ("movie", f"bowl/source/source-bowl-switcher-{offset:03d}"),
            ("original", f"bowl/replay/ref/bowl-next-switcher-{offset}"),
            ("native", f"bowl/replay/native/bowl-next-switcher-{offset}"),
        ):
            wram, sram = bytearray(131072), bytearray(8192)
            values = {
                "movie": (15, 5, 69),
                "original": (1, 5, 67),
                "native": (0, 4, 67),
            }
            c6, c8, other = values[side]
            wram[0xC6] = c6
            wram[0xC8] = c8
            wram[0x69] = other
            sram[0xC6 + census.OFFSET_CANDIDATE] = c6
            sram[0xC8 + census.OFFSET_CANDIDATE] = c8
            captured[side] = {"wram": bytes(wram), "sram": bytes(sram)}
            claim = (
                row["movie_original"] if side == "movie" else
                row["fresh_guests"].setdefault(side, {})
            )
            for kind, data in captured[side].items():
                members[f"{prefix}.{kind}.bin"] = data
                claim[kind+"_sha256"] = hashlib.sha256(data).hexdigest()
            if side != "movie":
                claim["absolute_host_frame"] = 984 + 3365 + offset
        for side in ("original", "native"):
            source = census.pair(captured["movie"], captured[side])
            claim = row["fresh_guests"][side]
            claim["wram_source_vs_guest"] = {
                "different_byte_count": source["unmasked_wram_different_byte_count"]}
            claim["sram_source_vs_guest"] = {
                "different_byte_count": source["unmasked_sram_different_byte_count"]}
        observations.append(row)
    members["bowl-report.json"] = json.dumps(report).encode()
    path = folder / "source-bowl-zip.zip"
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as z:
        for key, data in members.items():
            z.writestr(key, data)
    return path, members, hashlib.sha256(path.read_bytes()).hexdigest()


class SourceMovieSramCrosswalkTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path, self.members, self.digest = fixture(Path(folder.name))

    def repack(self, updates=None, removed=None):
        contents = dict(self.members)
        contents.update(updates or {})
        if removed:
            del contents[removed]
        with ZipFile(self.path, "w", compression=ZIP_DEFLATED) as z:
            for key, data in contents.items():
                z.writestr(key, data)
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_positive_is_a_complete_source_snapshot_but_never_admits_course(self):
        result = census.audit(self.path, self.digest)
        self.assertEqual(result["registered_original_movie_samples"], 8)
        self.assertEqual(result["release_usa_event_admissions"], 0)
        self.assertFalse(result["independent_first_writer_or_copy_direction_proven"])
        first = result["temporal_observations"][0]["cross_guest_pairs"]
        self.assertEqual(
            first["movie_vs_fresh_original"]["unmasked_wram_different_byte_count"], 2)
        self.assertEqual(
            first["movie_vs_fresh_original"][
                "wram_differences_matching_sram_at_plus_0xE6B"], 1)
        self.assertEqual(
            first["movie_vs_native"][
                "wram_differences_matching_sram_at_plus_0xE6B"], 2)
        self.assertEqual(
            first["fresh_original_vs_native"][
                "wram_differences_matching_sram_at_plus_0xE6B"], 2)
        self.assertEqual(first["movie_vs_fresh_original"][
            "first_16_unmatched_wram_differences"][0]["wram_address"], "7E:0069")
        self.assertEqual(first["movie_vs_native"]["masked_or_waived_wram_bytes"], 0)

    def test_untrusted_wrong_original_zip_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "ZIP SHA"):
            census.audit(self.path, "f"*64)

    def test_missing_movie_raw_image_denied_even_when_zip_digest_is_updated(self):
        target = "bowl/source/source-bowl-switcher-339.wram.bin"
        revised = self.repack(removed=target)
        with self.assertRaisesRegex(ValueError, "missing true source"):
            census.audit(self.path, revised)

    def test_mutated_guest_memory_denied_even_with_rehashed_zip(self):
        target = "bowl/replay/native/bowl-next-switcher-344.sram.bin"
        changed = bytearray(self.members[target]);changed[0xF31] ^= 5
        revised = self.repack({target: bytes(changed)})
        with self.assertRaisesRegex(ValueError, "hash disagrees"):
            census.audit(self.path, revised)

    def test_rehashed_forged_source_comparison_denied(self):
        report = json.loads(self.members["bowl-report.json"])
        report["bowl_source_movie_three_guest_memory"]["samples"][0][
            "fresh_guests"]["original"]["wram_source_vs_guest"][
                "different_byte_count"] = 0
        revised = self.repack({"bowl-report.json": json.dumps(report).encode()})
        with self.assertRaisesRegex(ValueError, "WRAM contradicts original producer"):
            census.audit(self.path, revised)

    def test_bad_source_clock_not_rebased_into_a_positive(self):
        report = json.loads(self.members["bowl-report.json"])
        report["bowl_source_movie_three_guest_memory"]["samples"][0][
            "movie_absolute_host_frame"] += 1
        revised = self.repack({"bowl-report.json": json.dumps(report).encode()})
        with self.assertRaisesRegex(ValueError, "host frame"):
            census.audit(self.path, revised)


if __name__ == "__main__":
    unittest.main()
