#!/usr/bin/env python3
"""ROM-free fail-closed five-stage Windows P2 recovery QA consumer tests.

These are fabricated source logs and profile bytes; they grant no real-game,
power-loss, hardware, reference-emulator or release acceptance.
"""
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
import check_baldosa_win32_p2_catalog_stage_qa as qa
from tests.unit.test_check_baldosa_win32_created_pair_raw_qa import profile_bytes


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def example_members():
    p1s, p1typed = profile_bytes("mike", 0)
    p2s, p2typed = profile_bytes("martin", 2)
    p1 = {qa.P1_FILES[0]: p1typed, qa.P1_FILES[1]: p1s}
    p2 = {qa.P2_FILES[0]: p2typed, qa.P2_FILES[1]: p2s, qa.P2_MUTEX: b""}
    stages = {}
    for index, stage in enumerate(qa.STAGES):
        files = dict(p1)
        files.update({
            qa.ROOT_FILES[0]: b"UR-HOST-STATE/6\nprofile=mike\n",
            qa.ROOT_FILES[1]: (qa.SINGLE_CATALOG if index in (0, 2)
                               else qa.DOUBLE_CATALOG),
        })
        if index:
            files.update(p2)
        stages[stage] = files
    source_report = {
        "scope": "four-real-windows-games-native-created-martin-recovered-catalog",
        "raw_source_archive": "ci-owned-p2-recovery-raw",
        "source_stage_manifest_names": list(qa.STAGES),
        "fault_cut": "ci-only-restore-original-single-row-catalog",
        "source_created_named_profiles": ["mike", "martin"],
        "first_and_second_real_p1_pad_handler": True,
        "third_real_p1_pad_handler_catalog_only_recovery": True,
        "fourth_real_guest_two_seat_stock_go": True,
        "unmodified_p2_typed_raw_mutex": True,
        "original_p1_selector_unchanged": True,
        "physical_os_crash_proven": False,
        "genuine_completed_match_proven_by_this_route": False,
        "physical_controller_hardware_proven": False,
        "release_gate_credit": 0,
    }
    root = r"C:\CI\Interrupted Native P2 Catalog Test Only"
    source = {"report.json": json.dumps(source_report).encode()}
    for i, name in enumerate(qa.SOURCE_LOGS):
        lines = (
            "[Gamepad] SDL reports 0 joystick(s). enable_gamepad=[1,1]",
            "[Launcher] Config/saves anchored to '" + root + "'.",
            "video=windows audio=dummy",
            *qa.EVENTS[i],
        )
        source[name] = ("\n".join(lines) + "\n").encode()
    return stages, source


def render_stages(stages: dict) -> dict[str, bytes]:
    out = {}
    for stage, files in stages.items():
        members = {p: {"sha256": sha(b), "bytes": len(b)}
                   for p, b in files.items()}
        report = {
            "schema": qa.SCHEMA, "stage": stage,
            "scope": "one-throwaway-Windows-CI-user-only",
            "source_profiles": (["mike"] if stage == qa.STAGES[0]
                                else ["mike", "martin"]),
            "members": members, "includes_rom": False,
            "includes_executable": False, "release_gate_credit": 0,
        }
        out[stage + "/manifest.json"] = json.dumps(report).encode()
        out.update({stage + "/" + p: b for p, b in files.items()})
    return out


def zip_members(path: Path, data: dict, *, link: str | None = None) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, body in data.items():
            if name == link:
                item = zipfile.ZipInfo(name)
                item.create_system = 3
                item.external_attr = 0o120777 << 16
                z.writestr(item, body)
            else:
                z.writestr(name, body)


class FiveStageIndependentReaderTest(unittest.TestCase):
    def evaluate(self, stages=None, source=None, *, source_link=None,
                 stage_link=None, corrupt_source_sha=False,
                 stage_members=None):
        if stages is None or source is None:
            exemplar, logs = example_members()
            stages = exemplar if stages is None else stages
            source = logs if source is None else source
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "actual-source.zip"
            after = Path(tmp) / "actual-raw-stages.zip"
            zip_members(before, source, link=source_link)
            zip_members(after, stage_members if stage_members is not None
                        else render_stages(stages), link=stage_link)
            return qa.audit_pair(
                before, after,
                expected_source_sha256=(
                    "0" * 64 if corrupt_source_sha else sha(before.read_bytes())),
                expected_stage_sha256=sha(after.read_bytes()))

    def test_positive_synthetic_five_stages_have_zero_release_credit(self):
        result = self.evaluate()
        self.assertEqual(result["stage_member_count"], 37)
        self.assertEqual(result["original_guest_stock_go_frame"], 2353)
        self.assertEqual(result["typed_original_stock_rider_ids"], [0, 2])
        self.assertTrue(result["native_p2_typed_raw_and_empty_mutex_equal_across_four_later_stages"])
        for k in ("power_loss_or_real_process_crash_verified",
                  "physical_two_gamepads_or_audible_audio_verified",
                  "one_final_merged_main_Windows_candidate_accepted",
                  "same_GitHub_Actions_run_verified_from_external_metadata"):
            self.assertFalse(result[k])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_missing_and_extraneous_snapshot_members_rejected(self):
        stages, source = example_members()
        original = render_stages(stages)
        for removed in ("after-p1-created/manifest.json",
                        "catalog-row-lost/profiles-v1.txt",
                        "after-source-go/" + qa.P2_MUTEX):
            with self.subTest(removed=removed):
                changed = dict(original)
                del changed[removed]
                with self.assertRaisesRegex(ValueError, "missing/extra/duplicated"):
                    self.evaluate(stages, source, stage_members=changed)
        added = dict(original)
        added["private-user-data.srm"] = b"PRIVATE"
        with self.assertRaisesRegex(ValueError, "missing/extra/duplicated"):
            self.evaluate(stages, source, stage_members=added)

    def test_resigned_catalog_or_original_p2_mutation_rejected(self):
        cases = (
            (qa.STAGES[2], qa.ROOT_FILES[1],
             qa.DOUBLE_CATALOG),
            (qa.STAGES[3], qa.P2_FILES[1],
             bytes([2]) * 8192),
            (qa.STAGES[4], qa.P2_MUTEX, b"unexpected"),
            (qa.STAGES[3], qa.ROOT_FILES[0],
             b"UR-HOST-STATE/6\nprofile=martin\n"),
            (qa.STAGES[2], qa.P1_FILES[1],
             bytes([1]) * 8192),
        )
        for stage, path, body in cases:
            with self.subTest(stage=stage, path=path):
                original, source = example_members()
                original[stage][path] = body
                with self.assertRaises(ValueError):
                    self.evaluate(original, source)

    def test_producer_stage_manifest_forged_release_or_profile_rejected(self):
        stages, source = example_members()
        for key, body in (
            ("release_gate_credit", 1),
            ("includes_rom", True),
            ("source_profiles", ["andrew"]),
            ("stage", "catalog-row-lost"),
        ):
            members = render_stages(stages)
            name = "after-p1-created/manifest.json"
            manifest = json.loads(members[name])
            manifest[key] = body
            members[name] = json.dumps(manifest).encode()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "manifest"):
                self.evaluate(stages, source, stage_members=members)

    def test_source_forged_or_missing_game_event_or_wrong_root_rejected(self):
        stages, source = example_members()
        for mutation in (
            ("third_native_p2_recovers/log.txt",
             "UR_BALDOSA_NATIVE_SECOND_RACER_RECOVERY restored=1",
             "UR_BALDOSA_NATIVE_SECOND_RACER_RECOVERY restored=0"),
            ("fourth_native_two_seat_go/log.txt",
             "script f=2353 dump go ok", "script f=2353 dump go failed"),
            ("second_native_martin/log.txt",
             r"C:\CI\Interrupted Native P2 Catalog Test Only",
             r"C:\Different\Interrupted Native P2 Catalog Test Only"),
        ):
            name, prev, repl = mutation
            changed = dict(source)
            changed[name] = changed[name].replace(prev.encode(), repl.encode())
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.evaluate(stages, changed)
        changed = dict(source)
        r = json.loads(changed["report.json"])
        r["physical_os_crash_proven"] = True
        changed["report.json"] = json.dumps(r).encode()
        with self.assertRaises(ValueError):
            self.evaluate(stages, changed)

    def test_native_created_rider_and_hardware_claim_cannot_be_forged(self):
        stages, source = example_members()
        mutations = (
            ("first_native_mike/log.txt",
             b"UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike",
             b"UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=1 id=andrew"),
            ("fourth_native_two_seat_go/log.txt",
             b"[Gamepad] SDL reports 0 joystick(s).",
             b"[Gamepad] SDL reports 2 joystick(s)."),
            ("fourth_native_two_seat_go/log.txt",
             b"video=windows audio=dummy",
             b"video=windows audio=wasapi"),
        )
        for name, old, new in mutations:
            changed = dict(source)
            changed[name] = changed[name].replace(old, new)
            with self.subTest(file=name, mutation=new), self.assertRaises(ValueError):
                self.evaluate(stages, changed)

    def test_exact_actions_sha_and_symlink_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.evaluate(corrupt_source_sha=True)
        stages, source = example_members()
        with self.assertRaisesRegex(ValueError, "linked"):
            self.evaluate(stages, source, stage_link="after-p2-created/" + qa.P2_MUTEX)
        with self.assertRaisesRegex(ValueError, "linked"):
            self.evaluate(stages, source, source_link="fourth_native_two_seat_go/log.txt")


if __name__ == "__main__":
    unittest.main()
