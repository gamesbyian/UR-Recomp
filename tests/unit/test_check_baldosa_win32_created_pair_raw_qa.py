#!/usr/bin/env python3
"""ROM-free adversarial tests for exact first-created 2P raw source bytes.

No test payload here is a real original emulator/Windows run. The independent
positive observation must come from a separate downloaded exact Windows ZIP.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_created_pair_raw_qa as qa
from tests.unit.test_check_baldosa_win32_six_ui_created_pair_records_qa import six
from verify_windows_tournament_acceptance_receipt import fnv_hex


RUN_NAME = "run-0001791957063228-0000.urrun"
INPUT = (
    "input 206 800 80 80",
    "input 1007 30 180 81",
    "input 1038 800 80 80",
    "input 1839 60 90 A0",
    "input 1900 331 80 80",
)


def record(*rows):
    body = ("\n".join(rows) + "\n").encode("ascii")
    return body + ("checksum " + fnv_hex(body) + "\n").encode("ascii")


def generated_run():
    return record(
        "URRUN 1", "game uniracers-usa",
        "rom_sha256 " + qa.USA_ROM_SHA256,
        "build_compat " + qa.BALDOSA_COMPAT,
        "course course:01", "mode race-2p",
        "elapsed_ticks60 1654", "frame_count 2231",
        "terminal_digest -", *INPUT, "END",
    )


def generated_match(run):
    checksum = qa.canonical_lines(run, qa.MAX_RUN_BYTES)[1]
    return record(
        "UR-MULTIPLAYER-MATCH/1",
        "run_checksum " + checksum,
        "course course:01", "outcome p2",
        "p1_result 2761", "p2_result 2757",
        "p1_profile 6d696b65", "p1_name 4d494b45", "p1_rider 0",
        "p2_profile 6d617274696e", "p2_name 4d415254494e",
        "p2_rider 2",
    )


def profile_bytes(name, rider):
    save = bytearray(8192)
    save[0x748] = rider
    source = (
        "UR-HOST-PROFILE/5\n" +
        f"profile={name}\n" +
        "generation=1\n" +
        "stock_sram=" + bytes(save).hex() + "\n" +
        f"racer_name={name.upper()}\n" +
        f"racer_index={rider}\n"
    ).encode("ascii")
    return bytes(save), source


def example_members():
    full = six()
    raw_report, *logs = copy.deepcopy(full)
    run = generated_run()
    match = generated_match(run)
    digest = lambda b: hashlib.sha256(b).hexdigest()
    raw_report["canonical_one_pair_sha256"] = {
        RUN_NAME: digest(run), RUN_NAME + ".urmatch": digest(match),
    }
    source = dict(zip(qa.SOURCE_GROUP, [
        json.dumps(raw_report).encode("utf-8"),
        *(s.encode("utf-8") for s in logs),
    ]))
    mike_save, mike_profile = profile_bytes("mike", 0)
    martin_save, martin_profile = profile_bytes("martin", 2)
    files = {
        "host-state-v1.txt":
            b"UR-HOST-STATE/6\nprofile=martin\n",
        "profiles-v1.txt":
            b"UR-PROFILE-CATALOG/1\nmike|0|MIKE\nmartin|2|MARTIN\n",
        "saves/profile-mike/host-profile.txt": mike_profile,
        "saves/profile-mike/save.srm": mike_save,
        "saves/profile-martin/host-profile.txt": martin_profile,
        "saves/profile-martin/save.srm": martin_save,
        "saves/save.srm": bytes(8192),
        "multiplayer-runs/" + RUN_NAME: run,
        "multiplayer-runs/" + RUN_NAME + ".urmatch": match,
    }
    manifest = {
        "schema": "baldosa-native-disposable-source-pair-v1",
        "scope": "one-throwaway-Windows-CI-user-only",
        "includes_executable": False, "includes_rom": False,
        "release_gate_credit": 0,
        "source_profiles": ["mike", "martin"],
        "source_pair": [RUN_NAME, RUN_NAME + ".urmatch"],
        "members": {
            name: {"bytes": len(raw), "sha256": digest(raw)}
            for name, raw in files.items()
        },
    }
    return {
        **source,
        **{qa.RAW_PREFIX + name: raw for name, raw in files.items()},
        qa.RAW_PREFIX + "manifest.json":
            (json.dumps(manifest, sort_keys=True) + "\n").encode("utf-8"),
    }


def write_test_zip(path, members):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, body in members.items():
            z.writestr(name, body)


def resign_payload(members, path, content):
    out = dict(members)
    out[qa.RAW_PREFIX + path] = content
    manifest_path = qa.RAW_PREFIX + "manifest.json"
    manifest = json.loads(out[manifest_path])
    manifest["members"][path] = {
        "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
    }
    out[manifest_path] = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    return out


class RawCreatedPairSource(unittest.TestCase):
    def evaluate(self, members):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "runtime.zip"
            write_test_zip(archive, members)
            return qa.audit_zip(archive)

    def test_synthetic_same_source_six_games_typed_profiles_and_pair_codecs(self):
        result = self.evaluate(example_members())
        self.assertTrue(result["typed_profiles_exactly_match_both_raw_SRAM"])
        self.assertEqual(result["rider_ids_from_independent_8192_byte_SRAM"], [0, 2])
        self.assertEqual(result["independently_decoded_source_input_frames"], 2231)
        self.assertEqual(result["independently_decoded_source_input_runs"], 5)
        self.assertFalse(result["physical_two_gamepads_and_real_audio_verified"])
        self.assertFalse(result["original_Snes9x_USA_complete_event_parity_proven"])
        self.assertFalse(result["pair_bytes_seen_both_before_and_after_records_independently"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_missing_sources_raw_members_and_wrong_nesting_fail(self):
        members = example_members()
        for name in (
            qa.SOURCE_GROUP[0], qa.SOURCE_GROUP[-1],
            qa.RAW_PREFIX + "manifest.json",
            qa.RAW_PREFIX + "saves/profile-martin/host-profile.txt",
            qa.RAW_PREFIX + "saves/profile-mike/save.srm",
            qa.RAW_PREFIX + "multiplayer-runs/" + RUN_NAME + ".urmatch",
        ):
            reduced = dict(members)
            reduced.pop(name)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.evaluate(reduced)
        extra = dict(members)
        extra[qa.RAW_PREFIX + "../private/save.srm"] = bytes(8192)
        with self.assertRaises(ValueError):
            self.evaluate(extra)

    def test_known_other_windows_groups_may_coexist_but_earn_no_raw_credit(self):
        from verify_baldosa_romless_candidate_qa import RUNTIME_ALLOWED_MEMBERS
        members = example_members()
        other = sorted(RUNTIME_ALLOWED_MEMBERS - set(qa.SOURCE_GROUP))
        self.assertGreaterEqual(len(other), 30)
        # Real #1536 uploads other genuine bounded log groups alongside the
        # created pair. Their source authenticity belongs to other readers.
        members.update({name: b"source-diagnostic" for name in other})
        result = self.evaluate(members)
        self.assertTrue(result["typed_profiles_exactly_match_both_raw_SRAM"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_known_outer_member_must_be_regular_and_bounded(self):
        from verify_baldosa_romless_candidate_qa import RUNTIME_ALLOWED_MEMBERS
        extra_name = sorted(RUNTIME_ALLOWED_MEMBERS - set(qa.SOURCE_GROUP))[0]
        members = example_members()
        members[extra_name] = b"source-diagnostic"
        self.evaluate(members)  # recognized companion group, no extra credit
        for malformed in (b"", b"Z" * (2 * 1024 * 1024 + 1)):
            changed = dict(members)
            changed[extra_name] = malformed
            with self.subTest(bytes=len(malformed)), self.assertRaisesRegex(
                    ValueError, "linked/directory/empty/oversized"):
                self.evaluate(changed)
        # Symlink with a permitted name is still an unsafe payload.
        with tempfile.TemporaryDirectory() as td:
            archive_path = Path(td) / "known-but-unsafe.zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as z:
                for name, contents in members.items():
                    if name == extra_name:
                        item = zipfile.ZipInfo(name)
                        item.create_system = 3
                        item.external_attr = (0o120777 << 16)
                        z.writestr(item, contents)
                    else:
                        z.writestr(name, contents)
            with self.assertRaisesRegex(ValueError, "linked/directory/empty/oversized"):
                qa.audit_zip(archive_path)

    def test_unrelated_outer_zip_members_fail_closed(self):
        # A valid guest/raw subgroup must not launder unreviewed source-root
        # material in the same ZIP. These are ROM-free synthetic adversaries.
        for name in (
            "private-user-data/save.srm",
            "untracked-windows.exe",
            "../outside/host-profile.txt",
            qa.PREFIX + "unexpected.log",
            qa.RAW_PREFIX[:-1] + "-sibling/saves/mike/save.srm",
        ):
            with self.subTest(unreviewed_name=name):
                members = example_members()
                members[name] = b"unreviewed-member"
                with self.assertRaisesRegex(ValueError, "unallowlisted Windows source ZIP"):
                    self.evaluate(members)

    def test_resigned_wrong_source_rider_pair_or_result_rejected(self):
        src = example_members()
        cases = (
            ("saves/profile-martin/save.srm", lambda b: b[:0x748] + b"\x01" + b[0x749:]),
            ("saves/profile-mike/host-profile.txt", lambda b: b.replace(
                b"racer_index=0", b"racer_index=2")),
            ("profiles-v1.txt", lambda b: b.replace(
                b"martin|2|MARTIN", b"martin|1|MARTIN")),
            ("host-state-v1.txt", lambda b: b.replace(
                b"profile=martin", b"profile=mike")),
            ("multiplayer-runs/" + RUN_NAME, lambda b: b.replace(
                b"frame_count 2231", b"frame_count 2232")),
            ("multiplayer-runs/" + RUN_NAME + ".urmatch", lambda b: b.replace(
                b"p2_profile 6d617274696e", b"p2_profile 616e64726577")),
        )
        for path, mutate in cases:
            with self.subTest(path=path):
                old = src[qa.RAW_PREFIX + path]
                revised = resign_payload(src, path, mutate(old))
                with self.assertRaises(ValueError):
                    self.evaluate(revised)

    def test_reported_sha_must_match_real_archived_pair(self):
        members = example_members()
        target = qa.RAW_PREFIX + "multiplayer-runs/" + RUN_NAME
        corrupt = dict(members)
        corrupt[target] = corrupt[target].replace(b"frame_count 2231",
                                                    b"frame_count 2232")
        with self.assertRaisesRegex(ValueError, "manifest hash"):
            self.evaluate(corrupt)

    def test_forged_gate_and_missing_source_match_not_promoted(self):
        members = example_members()
        path = qa.RAW_PREFIX + "manifest.json"
        altered = json.loads(members[path])
        altered["release_gate_credit"] = 1
        revised = dict(members)
        revised[path] = json.dumps(altered).encode()
        with self.assertRaises(ValueError):
            self.evaluate(revised)
        altered["release_gate_credit"] = 0
        revised[path] = json.dumps(altered).encode()
        report = json.loads(members[qa.SOURCE_GROUP[0]])
        report["native_existing_p1_profile_selector_UI_proved"] = False
        revised[qa.SOURCE_GROUP[0]] = json.dumps(report).encode()
        with self.assertRaises(ValueError):
            self.evaluate(revised)


if __name__ == "__main__":
    unittest.main()
