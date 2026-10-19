"""Synthetic ZIP fault cases for real Dragster original/native same-host archive audit."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_dragster_same_host_archive as audit


class DragsterSameHostArchiveTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.archive = self.root / "synthetic.zip"
        self.members = {}
        event = {
            "original_entry_frame": 794,
            "original_result_frame": 2874,
            "source_next_zoo": {"sample_offsets": list(audit.OFFSETS)},
        }
        hand = {
            "original_movie_zoo_entry_frame": 3190,
            "original_movie_zoo_entry_relative_to_dragster_result": 316,
            "release_complete_usa_event_credit": 0,
            "source_controller_masks_rephased": False,
            "all_three_guest_result_relative_entry_offsets_equal": False,
            "entry_brackets": {
                "original": {"exact_adjacent_onset_offset": 315},
                "native": {"exact_adjacent_onset_offset": 318},
            },
            "samples": [],
        }
        self.report = {
            "name": "dragster", "course_id": "course:01",
            "original_source_event": event,
            "dragster_next_zoo_handoff": hand,
            "reference_entry": 945, "native_entry": 945,
            "comparison": {
                "terminal_result_guest_frame": {
                    "reference_relative": 2081, "native_relative": 2079},
                "paired_event_candidate": False,
            },
        }
        logs = {"original": [], "native": []}
        for offset in audit.OFFSETS:
            row = {"offset_from_respective_dragster_result": offset,
                   "fresh_guests": {}}
            for side, folder, base, first_active in (
                    ("original", "ref", 3026, 315),
                    ("native", "native", 3024, 318)):
                tag = f"dragster-next-zoo-{offset:03d}"
                wram = bytearray(131072)
                wram[0xCE] = 1
                wram[0x313] = 1 if offset >= first_active else 0
                sram = bytes(8192)
                self.members[f"dragster/replay/{folder}/{tag}.wram.bin"] = bytes(wram)
                self.members[f"dragster/replay/{folder}/{tag}.sram.bin"] = sram
                row["fresh_guests"][side] = {
                    "host_frame": base + offset,
                    "full_wram_sha256": audit.digest(wram),
                    "full_sram_sha256": audit.digest(sram),
                    "menu": 0, "track": 1, "in_race": wram[0x313], "tour_row": 0,
                }
                logs[side].append(f"script f={base + offset} dump {tag} ok")
            hand["samples"].append(row)
        for side, name in (("original", "reference"), ("native", "native")):
            self.members[f"dragster/replay/{name}.log"] = (
                "\n".join(logs[side]) + "\n").encode("ascii")
        self.write()

    def write(self) -> str:
        self.members["dragster-report.json"] = json.dumps(self.report).encode("utf8")
        with ZipFile(self.archive, "w", ZIP_DEFLATED) as z:
            for name, data in self.members.items():
                z.writestr(name, data)
        return audit.digest(self.archive.read_bytes())

    def test_same_host_real_frames_are_not_result_relative_aligned(self):
        receipt = audit.analyze(self.archive, self.write())
        self.assertEqual(receipt["same_host_frames"],
                         [3338, 3340, 3341, 3342, 3343, 3344, 3345])
        self.assertEqual(receipt["fresh_guest_absolute_zoo_onsets"],
                         {"original": 3341, "native": 3342})
        pre = next(x for x in receipt["samples"]
                   if x["absolute_guest_host_frame"] == 3340)
        self.assertTrue(pre["named_state_equal"])
        edge = next(x for x in receipt["samples"]
                    if x["absolute_guest_host_frame"] == 3341)
        self.assertFalse(edge["named_state_equal"])
        self.assertEqual(edge["full_wram"]["differing_bytes"], 1)
        self.assertEqual(edge["full_wram"]["excluded_bytes"], 0)
        self.assertTrue(receipt["historical_movie_clock_not_equated_to_guest"])
        self.assertEqual(receipt["release_complete_event_credit"], 0)

    def test_archive_tamper_and_bad_actual_guest_clock_are_rejected(self):
        original_sha = self.write()
        name = "dragster/replay/ref/dragster-next-zoo-315.wram.bin"
        self.members[name] = bytes(131072)
        self.write()
        with self.assertRaisesRegex(audit.EvidenceError, "ZIP SHA256"):
            audit.analyze(self.archive, original_sha)
        with self.assertRaisesRegex(audit.EvidenceError, "memory SHA256"):
            audit.analyze(self.archive, audit.digest(self.archive.read_bytes()))
        self.setUp()
        name = "dragster/replay/reference.log"
        self.members[name] = self.members[name].replace(
            b"script f=3341 dump", b"script f=3342 dump")
        with self.assertRaisesRegex(audit.EvidenceError, "timestamp"):
            audit.analyze(self.archive, self.write())

    def test_movie_or_release_provenance_must_not_be_forged(self):
        self.report["original_source_event"]["original_result_frame"] = 2875
        with self.assertRaisesRegex(audit.EvidenceError, "inconsistent"):
            audit.analyze(self.archive, self.write())
        self.report["original_source_event"]["original_result_frame"] = 2874
        self.report["dragster_next_zoo_handoff"]["release_complete_usa_event_credit"] = 1
        with self.assertRaisesRegex(audit.EvidenceError, "inconsistent"):
            audit.analyze(self.archive, self.write())


if __name__ == "__main__":
    unittest.main()
