"""ROM-free negative cases for the genuine-shape Bowl post-result raw ZIP."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_bowl_temporal_delta_census as census


def synthetic_archive(root: Path):
    members = {}
    report = {
        "name": "bowl", "course_id": "course:03",
        "rom_sha256": "a"*64, "original_movie_sha256": "b"*64,
        "native_executable_sha256": "c"*64,
        "original_source_event": {
            "original_entry_frame": 8620, "original_result_frame": 11985},
        "bowl_next_switcher_handoff": {
            "source_next_switcher_entry_offset": 342,
            "source_controller_masks_modified": False,
            "sample_offsets": list(census.OFFSETS), "samples": []},
    }
    primary = report["bowl_next_switcher_handoff"]
    independent = {
        "case": "bowl", "observed_raw_wram_sram_pairs": 12,
        "accepted_event_credit": 0,
        "independent_complete_usa_event_adjudication": "HOLD",
        "checked_samples": [],
    }
    total = 0
    for offset in census.OFFSETS:
        guests = {}
        for side, label in (("ref", "original"), ("native", "native")):
            sram = bytearray(8192)
            wram = bytearray(131072)
            if side == "ref":
                for address, value in ((0xEF6, 1), (0xF31, 1), (0xF33, 5)):
                    sram[address] = value
                wram[0xC6] = 1
                wram[0xC8] = 5
                if offset >= 340:
                    wram[0x83] = 22
                if offset >= 341:
                    wram[0x84] = 15
            else:
                sram[0xF33] = 4
                wram[0xC8] = 4
            for kind, data in (("sram", sram), ("wram", wram)):
                members[
                    f"bowl/replay/{side}/bowl-next-switcher-{offset}.{kind}.bin"
                ] = bytes(data)
            guests[label] = {
                "actual_host_frame": 4683 + offset - 334,
                "sram_sha256": hashlib.sha256(sram).hexdigest(),
                "wram_sha256": hashlib.sha256(wram).hexdigest(),
            }
        delta = 2 + (offset >= 340) + (offset >= 341)
        total += delta
        primary["samples"].append({
            "offset_from_observed_bowl_result": offset,
            "fresh_guests": guests,
            "full_sram_differing_byte_count": 3,
            "triplet_named_states_equal": offset not in (341, 342, 343),
            "full_wram_byte_difference": {"differing_byte_count": delta},
        })
        independent["checked_samples"].append({
            "offset": offset, "unmasked_wram_differing_bytes": delta,
            "full_sram_equal": False,
        })
    independent["raw_unmasked_wram_differing_byte_occurrences"] = total
    raw = json.dumps(report).encode()
    independent["producer_sha256"] = hashlib.sha256(raw).hexdigest()
    members["bowl-report.json"] = raw
    members["bowl-independent-raw-audit.json"] = json.dumps(
        independent).encode()
    zip_path = root / "bowl-synthetic.zip"
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return zip_path, hashlib.sha256(zip_path.read_bytes()).hexdigest(), members


class BowlTemporalCensusTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.archive, self.digest, self.members = synthetic_archive(self.root)

    def rewrite(self, *, changed=None, missing=None):
        source = dict(self.members)
        if missing is not None:
            source.pop(missing)
        if changed is not None:
            source.update(changed)
        with ZipFile(self.archive, "w", compression=ZIP_DEFLATED) as archive:
            for name, content in source.items():
                archive.writestr(name, content)
        return hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def test_valid_complete_synthetic_archive_is_always_no_admission(self):
        result = census.audit(self.archive, self.digest)
        self.assertEqual(result["samples_and_raw_memory_verified"], 12)
        self.assertTrue(result["sram_differences_same_addresses_values_all_samples"])
        self.assertEqual(
            result["temporal_observations"][0]["full_128k_wram_differing_bytes"], 2)
        self.assertEqual(result["usa_event_admissions"], 0)
        self.assertFalse(result["causal_mirror_or_writer_proven"])

    def test_wrong_original_archive_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, "ZIP SHA256"):
            census.audit(self.archive, "f"*64)

    def test_mutated_unmasked_guest_memory_rejected_even_if_zip_rehashed(self):
        name = "bowl/replay/ref/bowl-next-switcher-334.wram.bin"
        corrupted = bytearray(self.members[name])
        corrupted[3] = 7
        digest = self.rewrite(changed={name: bytes(corrupted)})
        with self.assertRaisesRegex(ValueError, "hash contradicts genuine producer"):
            census.audit(self.archive, digest)

    def test_missing_original_native_memory_file_is_not_an_event(self):
        name = "bowl/replay/native/bowl-next-switcher-354.sram.bin"
        digest = self.rewrite(missing=name)
        with self.assertRaisesRegex(ValueError, "missing authentic source capture"):
            census.audit(self.archive, digest)

    def test_rehashed_but_forged_original_source_result_frame_rejected(self):
        original = json.loads(self.members["bowl-report.json"])
        original["original_source_event"]["original_result_frame"] = 12345
        digest = self.rewrite(changed={
            "bowl-report.json": json.dumps(original).encode()})
        with self.assertRaises(ValueError):
            census.audit(self.archive, digest)


if __name__ == "__main__":
    unittest.main()
