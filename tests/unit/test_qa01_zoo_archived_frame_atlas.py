"""ROM-free negative fixtures; only pinned real Actions ZIP earns authentic label."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from tests.unit.test_qa01_independent_zoo_capture_ab_archive import SourceAuthenticAB
import qa01_independent_zoo_capture_ab_archive as original
import qa01_zoo_archived_frame_atlas as producer


class ArchivedDeltaAtlasTests(unittest.TestCase):
    def setUp(self):
        # Reuse the existing strict source/archive adversarial fixture without
        # inheriting or rerunning its own unrelated TestCase methods.
        SourceAuthenticAB.setUp(self)

    def case(self, mutation=None):
        members = dict(self.members)
        if mutation is not None:
            mutation(members)
        zip_path = self.root / "bounded.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in members.items():
                z.writestr(name, data)
        return producer.audit(
            zip_path,
            expected_sha=hashlib.sha256(zip_path.read_bytes()).hexdigest())

    def test_real_raw_reopen_and_missing_equal_frame_stays_unknown(self):
        report = self.case()
        self.assertEqual(report["independent_original_native_archive_adjudication"],
                         "HOLD")
        atlas = report["atlas"]
        self.assertEqual(
            atlas["full_original_native_raw_frame_pairs_independently_reopened"], 2)
        self.assertEqual(
            atlas["equal_digest_only_frame_pairs_not_independently_reopened"], [1])
        self.assertIsNone(atlas["timeline"][1]["original_native_observed_deltas"])
        self.assertIsNone(atlas["timeline"][2]["intra_guest_changes_since_previous"])
        self.assertEqual(
            atlas["per_address_occurrences"]["7E:0063"]["frames"], [2])
        self.assertEqual(
            atlas["unmasked_original_native_byte_occurrences"],
            {"wram": 1, "sram": 0})
        self.assertFalse(report["genuinely_consumed_CPU_or_SPC_divergence_proven"])
        self.assertEqual(report["accepted_USA_events"], 0)

    def test_wrong_zip_pin_rejected_before_any_raw_story(self):
        report = self.case()
        self.assertTrue(report["source_zip_sha256"])
        with zipfile.ZipFile(self.root / "bounded.zip", "a") as z:
            z.writestr("extra.txt", "mutated")
        with self.assertRaisesRegex(ValueError, "source ZIP SHA256"):
            producer.audit(self.root / "bounded.zip",
                           expected_sha=report["source_zip_sha256"])

    def test_missing_source_member_and_modified_original_bytes_fail_closed(self):
        prefix = original.RAW + "retained/"
        name = prefix + "native-relative-000002-wram.bin"
        for mode in ("missing", "modified"):
            def modify(members):
                if mode == "missing":
                    members.pop(name)
                else:
                    altered = bytearray(members[name])
                    altered[0x63] ^= 0x10
                    members[name] = bytes(altered)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.case(modify)

    def test_forged_green_gameplay_claim_rejected_even_if_zip_rehashed(self):
        def mutate(members):
            target = json.loads(members[original.DOC["on"]])
            target["comparison"]["paired_event_candidate"] = True
            members[original.DOC["on"]] = json.dumps(target).encode()
        with self.assertRaises(ValueError):
            self.case(mutate)


if __name__ == "__main__":
    unittest.main()
