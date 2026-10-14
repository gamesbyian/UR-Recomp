#!/usr/bin/env python3
"""ROM-free adversarial pre/post ZIP-consumer tests: no original gameplay credit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_pair_pre_post_qa as subject
import check_baldosa_win32_created_pair_raw_qa as qa
from tests.unit.test_check_baldosa_win32_created_pair_raw_qa import (
    RUN_NAME, example_members,
)


RUN = "multiplayer-runs/" + RUN_NAME
MATCH = RUN + ".urmatch"
SHA = lambda body: hashlib.sha256(body).hexdigest()


def fixture_pair():
    main = example_members()
    body = {
        RUN: main[qa.RAW_PREFIX + RUN],
        MATCH: main[qa.RAW_PREFIX + MATCH],
    }
    manifest = {
        "schema": subject.PRE_SCHEMA,
        "stage": subject.PRE_STAGE,
        "scope": subject.PRE_SCOPE,
        "source_profiles": ["mike", "martin"],
        "source_pair": [RUN_NAME, RUN_NAME + ".urmatch"],
        "includes_rom": False, "includes_executable": False,
        "release_gate_credit": 0,
        "members": {
            name: {"sha256": SHA(raw), "bytes": len(raw)}
            for name, raw in body.items()
        },
    }
    pre = {"manifest.json": json.dumps(manifest).encode(), **body}
    return pre, main


def write_zip(path: Path, members: dict, linked: str = "") -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in members.items():
            if name == linked:
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = 0o120777 << 16
                archive.writestr(info, value)
            else:
                archive.writestr(name, value)


class ArchivedPrePostIndependentQA(unittest.TestCase):
    def check(self, pre: dict, post: dict, *, wrong_before: bool = False,
              linked: str = ""):
        with tempfile.TemporaryDirectory() as root:
            a, b = Path(root) / "before.zip", Path(root) / "after.zip"
            write_zip(a, pre, linked=linked)
            write_zip(b, post)
            digest_a = SHA(a.read_bytes())
            return subject.audit_pair(
                a, b,
                expected_before_sha256=("0" * 64 if wrong_before else digest_a),
                expected_after_sha256=SHA(b.read_bytes()))

    def test_synthetic_full_source_and_separate_archived_pair_equal(self):
        pre, post = fixture_pair()
        result = self.check(pre, post)
        self.assertTrue(result["independently_compared_archived_run_and_sidecar_bytes_equal"])
        self.assertTrue(result["source_six_actual_native_processes_and_raw_pair_decoded"])
        self.assertEqual(result["source_scored_winner"], 2)
        self.assertEqual(result["source_hundredths"], [2761, 2757])
        self.assertEqual(result["release_gate_credit"], 0)
        for missing_acceptance in (
            "source_stage_before_first_records_independently_timestamped",
            "same_GitHub_Actions_run_provenance_independently_verified",
            "physical_two_gamepads_and_live_audio_verified",
            "original_Snes9x_USA_complete_event_parity_proven",
            "final_merged_main_Windows_release_candidate_nominated",
        ):
            self.assertFalse(result[missing_acceptance])

    def test_synthetic_missing_extra_or_private_member_rejected(self):
        pre, post = fixture_pair()
        for name in ("manifest.json", RUN, MATCH):
            shorter = dict(pre)
            del shorter[name]
            with self.subTest(missing=name), self.assertRaises(ValueError):
                self.check(shorter, post)
        for name in ("private-player.srm", "../outside.txt", "Uniracers-USA.sfc",
                     "other.exe", "ci-owned-raw-artifacts/host-state-v1.txt"):
            extra = dict(pre)
            extra[name] = b"PRIVATE"
            with self.subTest(extra=name), self.assertRaisesRegex(ValueError, "unreviewed"):
                self.check(extra, post)

    def test_synthetic_changed_pair_with_resigned_pre_manifest_still_rejected(self):
        pre, post = fixture_pair()
        modified = dict(pre)
        modified[RUN] = modified[RUN] + b"extra"
        m = json.loads(modified["manifest.json"])
        m["members"][RUN] = {"sha256": SHA(modified[RUN]), "bytes": len(modified[RUN])}
        modified["manifest.json"] = json.dumps(m).encode()
        with self.assertRaisesRegex(ValueError, "differ across Records viewers"):
            self.check(modified, post)

    def test_synthetic_modified_sidecar_with_resigned_pre_manifest_rejected(self):
        pre, post = fixture_pair()
        modified = dict(pre)
        modified[MATCH] = modified[MATCH] + b"x"
        m = json.loads(modified["manifest.json"])
        m["members"][MATCH] = {"sha256": SHA(modified[MATCH]), "bytes": len(modified[MATCH])}
        modified["manifest.json"] = json.dumps(m).encode()
        with self.assertRaisesRegex(ValueError, "differ across Records viewers"):
            self.check(modified, post)

    def test_producer_pre_manifest_cannot_claim_release_or_wrong_stage(self):
        pre, post = fixture_pair()
        for key, value in [
            ("release_gate_credit", 1),
            ("stage", "after-records"),
            ("includes_rom", True),
            ("includes_executable", True),
            ("source_profiles", ["mike", "andrew"]),
            ("source_pair", [RUN_NAME, "other.urrun.urmatch"]),
        ]:
            mutated = dict(pre)
            obj = json.loads(mutated["manifest.json"])
            obj[key] = value
            mutated["manifest.json"] = json.dumps(obj).encode()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "manifest"):
                self.check(mutated, post)

    def test_synthetic_source_CI_bytes_are_not_a_substitute_for_real_original_log(self):
        pre, post = fixture_pair()
        bad_post = dict(post)
        del bad_post[qa.SOURCE_GROUP[3]]
        with self.assertRaises(ValueError):
            self.check(pre, bad_post)

    def test_outer_actions_hash_mismatch_rejected(self):
        pre, post = fixture_pair()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.check(pre, post, wrong_before=True)

    def test_symlink_zip_member_rejected(self):
        pre, post = fixture_pair()
        with self.assertRaisesRegex(ValueError, "linked"):
            self.check(pre, post, linked=RUN)

    def test_post_zip_unreviewed_member_rejected_by_merged_reader(self):
        pre, post = fixture_pair()
        extra = dict(post)
        extra["private/not-allowed.srm"] = b"private"
        with self.assertRaisesRegex(ValueError, "unallowlisted Windows source ZIP"):
            self.check(pre, extra)


if __name__ == "__main__":
    unittest.main()
