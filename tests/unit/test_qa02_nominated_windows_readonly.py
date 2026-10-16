#!/usr/bin/env python3
"""Small QA oracle checks; real Windows attribute fault is Actions-only."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_nominated_windows_readonly as qa
from verify_retained_owner_playtest import SOURCE_COMMIT, CANDIDATE_SHA256, EXE_SHA256


class OriginalWindowsReadonlyTests(unittest.TestCase):
    def test_byte_inventory_is_source_owned_and_requires_full_raw(self):
        self.assertEqual(set(qa.FILES), {"raw", "typed", "selector", "catalog"})
        self.assertEqual(len(set(qa.FILES.values())), 4)
        self.assertEqual(SOURCE_COMMIT, "11501a15dea38fa912335cfc63103ce3a7208001")
        self.assertEqual(CANDIDATE_SHA256,
                         "5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7")
        self.assertEqual(EXE_SHA256,
                         "0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for label, name in qa.FILES.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"A" * (8192 if label == "raw" else 7))
            before = qa.take(root)
            self.assertEqual(qa.compare(before, before)["raw"]["changed"], 0)
            (root / qa.FILES["raw"]).write_bytes(b"B" * 8192)
            after = qa.take(root)
            changes = qa.compare(before, after)
            self.assertEqual(changes["raw"]["changed"], 8192)
            self.assertEqual(changes["typed"]["changed"], 0)
            self.assertEqual(changes["raw"]["before_sha256"],
                             hashlib.sha256(b"A" * 8192).hexdigest())
            (root / qa.FILES["raw"]).write_bytes(b"C" * 8191)
            with self.assertRaisesRegex(ValueError, "Invalid named-profile"):
                qa.compare(qa.take(root), before)

    def test_win32_readonly_attribute_failure_is_not_silently_ignored(self):
        with mock.patch.object(qa.subprocess, "run") as runner:
            runner.return_value.returncode = 0
            qa.attrib(Path("C:/fixture/save.srm"), "+R")
            self.assertEqual(runner.call_args.args[0][0], "attrib")
            self.assertEqual(runner.call_args.args[0][1], "+R")
            runner.return_value.returncode = 1
            runner.return_value.stdout = "denied"
            runner.return_value.stderr = ""
            with self.assertRaisesRegex(RuntimeError, "attrib"):
                qa.attrib(Path("C:/fixture/save.srm"), "-R")

    def test_win32_acl_uses_explicit_principal_and_fails_closed(self):
        sid = "S-1-5-21-123-456-789-1001"
        with mock.patch.object(qa.subprocess, "run") as runner:
            runner.return_value.stdout = "Successfully processed 3 files; Failed processing 0 files"
            runner.return_value.stderr = ""
            runner.return_value.returncode = 0
            qa.acl(Path("C:/root/profile-native-ci-rider"), sid, deny=True)
            argv = runner.call_args.args[0]
            self.assertEqual(argv[0], "icacls")
            self.assertIn("/deny", argv)
            self.assertIn(f"*{sid}:(WD,AD,WEA,WA,DE,DC)", argv)
            self.assertIn("/T", argv)
            qa.acl(Path("C:/root/profile-native-ci-rider"), sid, deny=False)
            self.assertIn("/remove:d", runner.call_args.args[0])
            self.assertIn(f"*{sid}", runner.call_args.args[0])
            runner.return_value.returncode = 5
            with self.assertRaisesRegex(RuntimeError, "icacls"):
                qa.acl(Path("C:/root/profile-native-ci-rider"), sid, deny=True)
        with self.assertRaisesRegex(ValueError, "native Windows SID"):
            qa.acl(Path("C:/root"), "administrator", deny=True)

    def test_denial_probe_must_actually_refuse_file_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            profile = Path(temp)
            with self.assertRaisesRegex(ValueError, "did not actually deny"):
                qa.require_os_denial(profile)
            self.assertFalse((profile / "_qa02_acl_probe_do_not_commit.txt").exists())
            with mock.patch.object(Path, "open", side_effect=PermissionError("denied")):
                self.assertIsNone(qa.require_os_denial(profile))
            self.assertFalse((profile / "_qa02_acl_probe_do_not_commit.txt").exists())

    def test_sid_is_parsed_from_actual_windows_whoami_principal(self):
        with mock.patch.object(qa.subprocess, "run") as runner:
            runner.return_value.stdout = '"WIN\\runneradmin","S-1-5-21-123-456-789-1001"\n'
            self.assertEqual(qa.current_sid(), "S-1-5-21-123-456-789-1001")
            self.assertEqual(runner.call_args.args[0], ["whoami", "/user", "/fo", "csv", "/nh"])
            runner.return_value.stdout = "bad principal"
            with self.assertRaisesRegex(ValueError, "unique Windows runner SID"):
                qa.current_sid()

    def test_real_win32_raw_file_acl_does_not_deny_profile_directory(self):
        sid = "S-1-5-21-123-456-789-1001"
        filename = Path("C:/disposable/profile-native-ci-rider/save.srm")
        with mock.patch.object(qa.subprocess, "run") as runner:
            runner.return_value.returncode = 0
            runner.return_value.stdout = "Successfully processed 1 files; Failed processing 0 files"
            runner.return_value.stderr = ""
            qa.deny_raw_write_only(filename, sid, deny=True)
            argv = runner.call_args.args[0]
            self.assertEqual(argv, ["icacls", str(filename), "/deny", f"*{sid}:(WD)"])
            self.assertNotIn("/T", argv)
            qa.deny_raw_write_only(filename, sid, deny=False)
            self.assertEqual(runner.call_args.args[0],
                             ["icacls", str(filename), "/remove:d", f"*{sid}"])
            runner.return_value.returncode = 5
            with self.assertRaisesRegex(RuntimeError, "raw-file icacls"):
                qa.deny_raw_write_only(filename, sid, deny=True)
        with self.assertRaisesRegex(ValueError, "native Windows SID"):
            qa.deny_raw_write_only(filename, "UNKNOWN", deny=True)

    def test_raw_write_denial_probes_os_without_changing_full_original_sram(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "save.srm"
            baseline = bytes(range(256)) * 32
            file.write_bytes(baseline)
            with self.assertRaisesRegex(ValueError, "remains writable"):
                qa.require_raw_write_denied(file, baseline)
            self.assertEqual(file.read_bytes(), baseline)
            with mock.patch.object(Path, "open", side_effect=PermissionError("Access denied")):
                self.assertIsNone(qa.require_raw_write_denied(file, baseline))
            self.assertEqual(file.read_bytes(), baseline)
            with self.assertRaisesRegex(ValueError, "baseline changed"):
                qa.require_raw_write_denied(file, b"not 8192 bytes")

    def test_raw_acl_original_executable_route_is_branch_isolated(self):
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
                    ).read_text(encoding="utf-8")
        self.assertIn("qa/qa02-original-win32-raw-file-write-denial-20261016", workflow)
        self.assertIn("--fault acl-denied-raw-file", workflow)
        self.assertIn("12016101293", workflow)
        self.assertIn("tools/qa02_nominated_windows_readonly.py", workflow)
        source = (ROOT / "tools/qa02_nominated_windows_readonly.py"
                  ).read_text(encoding="utf-8")
        self.assertIn("actual_native_write_rejected_after_preflight", source)
        self.assertIn("native_save_failed", source)
        self.assertIn("native_save_preflight_failed", source)
        self.assertIn("release_gate_credit\": 0", source)

    def test_win32_argv_uses_actual_executable_original_rom_and_existing_script(self):
        with mock.patch.object(qa.subprocess, "run") as runner:
            runner.return_value.returncode = 7
            runner.return_value.stdout = "save refused"
            runner.return_value.stderr = "profile unchanged"
            rc, log = qa.run_game(
                Path("C:/owner/UniracersSNESRecomp.exe"),
                Path("C:/reference/Uniracers_USA.sfc"),
                Path("C:/input/race_2p_split.txt"),
                Path("C:/qa/config.ini"), Path("C:/qa/root"), {"KEY": "VALUE"})
            self.assertEqual(rc, 7)
            self.assertIn("save refused", log)
            self.assertIn("profile unchanged", log)
            args = runner.call_args.args[0]
            self.assertEqual(args[0], "C:/owner/UniracersSNESRecomp.exe")
            self.assertIn("--no-launcher", args)
            self.assertIn("--script", args)
            self.assertEqual(args[-1], "C:/reference/Uniracers_USA.sfc")
            self.assertEqual(runner.call_args.kwargs["env"], {"KEY": "VALUE"})

    def test_one_branch_only_exact_owner_step_no_second_windows_framework(self):
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
                    ).read_text(encoding="utf-8")
        script = (ROOT / "tools/qa02_nominated_windows_readonly.py"
                  ).read_text(encoding="utf-8")
        self.assertIn("qa02-exact-owner-readonly-write-fault-20261016", workflow)
        self.assertIn("--retained", workflow)
        self.assertIn("12016101293", workflow)
        self.assertIn("tools/qa02_nominated_windows_readonly.py", workflow)
        self.assertIn("physical_player_notice_verified\": False", script)
        self.assertIn("actual_power_cut_or_disk_full\": False", script)
        self.assertIn("release_gate_credit\": 0", script)


if __name__ == "__main__":
    unittest.main()
