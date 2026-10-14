#!/usr/bin/env python3
"""ROM-free forged/invalid Practice artifact reader tests; no guest pass claim."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_baldosa_win32_practice_hardkill_qa import (
    FILES, GO, RESTORE, SANDBOX, SOURCEMARK, audit_archive
)

HEADER = ("[Launcher] Config/saves anchored to 'C:\\QA User'.\n"
          "[Gamepad] SDL reports 0 joystick(s). enable_gamepad=[1,1]\n")
NAMED = "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
SRC = SANDBOX + "\n" + SOURCEMARK + "\n" + "script f=1149 until 00E1F ok after 1 frames\n"
BOOT = "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv={}\n"


def sample(*, changed=True):
    out = {
        FILES[0]: HEADER + SRC + RESTORE + "\n",
        FILES[1]: HEADER + "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
                  "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike activation=next_process\n",
        FILES[2]: HEADER + NAMED + BOOT.format("aaaaaaaa") + SRC + RESTORE +
                  "\nUR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=unchanged\n",
        FILES[3]: HEADER + NAMED + BOOT.format("aaaaaaaa") + SRC,
        FILES[4]: json.dumps({
            "kill_method": "subprocess.Popen.kill (TerminateProcess on Windows)",
            "killed_while_alive": True, "process_returncode": 1,
            "script_quit_or_normal_shutdown": False, "script_token_seen": True,
        }),
        FILES[5]: HEADER + NAMED + BOOT.format("aaaaaaaa") +
                  ("UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n" if changed else "") +
                  "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=" +
                  ("committed" if changed else "unchanged") + "\n",
        FILES[6]: HEADER + NAMED + BOOT.format("bbbbbbbb" if changed else "aaaaaaaa") +
                  SRC + RESTORE + "\nUR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=committed\n",
    }
    return {key: val.encode() for key, val in out.items()}


def audit_fixture(directory, rows):
    p = Path(directory) / "synthetic.zip"
    with zipfile.ZipFile(p, "w") as z:
        for name, data in rows.items():
            z.writestr(name, data)
    return audit_archive(p, expected_sha256=hashlib.sha256(p.read_bytes()).hexdigest())


class PracticeArchiveReaderTest(unittest.TestCase):
    def test_distinguish_real_kill_from_interposed_ordinary_career(self):
        with tempfile.TemporaryDirectory() as d:
            r = audit_fixture(d, sample())
            self.assertTrue(r["actual_live_Windows_TerminateProcess_logged"])
            self.assertTrue(r["intervening_ordinary_career_play"])
            self.assertEqual(r["source_classification"],
                             "intervening_normal_career_game_changed_SRAM_before_Practice")
            self.assertFalse(r["independently_proven_full_named_byte_immutability"])
            self.assertEqual(r["release_gate_credit"], 0)

    def test_short_no_career_reboot_is_distinct(self):
        with tempfile.TemporaryDirectory() as d:
            r = audit_fixture(d, sample(changed=False))
            self.assertFalse(r["intervening_ordinary_career_play"])
            self.assertEqual(r["source_classification"],
                             "readmitted_Practice_boots_same_source_SRAM")

    def test_invalid_kills_sources_roots_results_and_archives_rejected(self):
        valid = sample()
        bad = []
        def mutated(name, before, after):
            d = dict(valid)
            d[name] = d[name].replace(before.encode(), after.encode())
            return d
        bad.extend((
            mutated(FILES[2], "fnv=aaaaaaaa", "fnv=11111111"),
            mutated(FILES[3], "original_course=1", "original_course=2"),
            mutated(FILES[3], "00E1F ok", "00E1E ok"),
            mutated(FILES[3], SANDBOX, "practice_sram_sandbox=0"),
            mutated(FILES[3], "C:\\QA User", "C:\\Other User"),
            mutated(FILES[2], "status=unchanged", "status=committed"),
            mutated(FILES[6], RESTORE, "practice_sram_restored=0"),
            mutated(FILES[6], "0 joystick(s)", "1 joystick(s)"),
            mutated(FILES[3], "script f=1149", "script f=1149 quit\nscript f=1149"),
        ))
        for changed in ({"killed_while_alive": False}, {"process_returncode": 0},
                        {"script_token_seen": False}, {"script_quit_or_normal_shutdown": True}):
            d = dict(valid)
            receipt = json.loads(d[FILES[4]])
            receipt.update(changed)
            d[FILES[4]] = json.dumps(receipt).encode()
            bad.append(d)
        d = dict(valid); d.pop(FILES[4]); bad.append(d)
        d = dict(valid); d["saves/private.srm"] = b"private"; bad.append(d)
        d = dict(valid); d[FILES[3]] += b"UR_BALDOSA_NATIVE_RUN CAPTURED=1\n"; bad.append(d)
        with tempfile.TemporaryDirectory() as folder:
            for n, rows in enumerate(bad):
                with self.subTest(case=n), self.assertRaises(ValueError):
                    audit_fixture(folder, rows)

    def test_full_external_zip_sha_required(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "synthetic.zip"
            with zipfile.ZipFile(p, "w") as z:
                for name, contents in sample().items():
                    z.writestr(name, contents)
            for digest in ("", "bad", "0" * 64):
                with self.subTest(digest=digest), self.assertRaises(ValueError):
                    audit_archive(p, expected_sha256=digest)


if __name__ == "__main__":
    unittest.main()
