#!/usr/bin/env python3
"""ROM-free QA-only negative tests of canonical original Win32 S evidence."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[2] / "tools/check_qa02_win32_interactive_s_original.py"
spec = importlib.util.spec_from_file_location("qawin32s", SCRIPT)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def profile(identity: str, raw: bytes) -> bytes:
    return (b"UR-HOST-PROFILE/5\nprofile=" + identity.encode() +
            b"\nstock_sram=" + raw.hex().encode() + b"\n")


def make_fixture():
    stock = b"ASJIver3.30" + bytes(8192 - 11)
    a = bytearray(stock)
    a[0x711] ^= 0x35
    b = bytearray(stock)
    b[0x712] ^= 0x25
    c = bytearray(stock)
    c[0x713] ^= 0x24
    a, b, c = bytes(a), bytes(b), bytes(c)
    selector = (b"UR-HOST-STATE/6\nprofile=native-ci-rider\n"
                b"display_mode=windowed\nvsync=on\n")
    selected = selector.replace(
        b"profile=native-ci-rider\n", b"profile=native-ci-second\n")
    catalog = (b"UR-PROFILE-CATALOG/1\n"
               b"native-ci-rider|0|MIKE\n"
               b"native-ci-second|2|MARTIN\n"
               b"native-ci-third|3|C\n")
    before = {
        "selector": selector, "catalog": catalog, "a-raw": a,
        "a-typed": profile("native-ci-rider", stock),
        "b-raw": b, "b-typed": profile("native-ci-second", b),
        "c-raw": c,
    }
    after = dict(before)
    after["selector"] = selected
    files = {}
    receipts = {}
    for stage, group in (("before-S", before), ("after-S", after),
                         ("cold1-S", after), ("cold2-S", after)):
        for label, contents in group.items():
            name = stage + "." + label + ".bin"
            files["source-bytes/" + name] = contents
            receipts[name] = {"bytes": len(contents), "sha256": sha(contents)}
    special = profile("native-ci-third", c)
    files["source-bytes/unrelated-C-original-typed.bin"] = special
    receipts["unrelated-C-original-typed.bin"] = {
        "bytes": len(special), "sha256": sha(special)}
    cmd = sha(b"original packaged launcher")
    report = {
        "schema": "ur-win32-interactive-original-cmd-s/1",
        "original_actual_cmd_sha256": cmd,
        "original_native_fixture_sha256": sha(b"fixture"),
        "original_seed_sha256": sha(stock),
        "actual_win32_console_choice": "S",
        "literal_win32_console_profile_text": "native-ci-second",
        "original_cmd_committed_once": True,
        "original_native_guest_B_cold_boot_count": 2,
        "damaged_A_untouched": True, "healthy_B_untouched": True,
        "unrelated_broken_C_untouched": True,
        "only_authorized_selector_changed": True,
        "all_retained_source_bytes": receipts,
        "release_gate_credit": 0,
        "physical_operator": False,
    }
    files["interactive-s-result.json"] = (
        json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    files["fixture.log"] = (
        b"UR_BALDOSA_NATIVE_PROFILE_FIXTURE A\n"
        b"UR_BALDOSA_NATIVE_PROFILE_FIXTURE B\n"
        b"UR_BALDOSA_NATIVE_PROFILE_FIXTURE C\n")
    files["interactive-S.log"] = (
        b"UR-BALDOSA-STARTUP-PROFILE-REJECTED: source\n"
        b"Explicit recovery choice [R/T/S/Q]: S\n"
        b"Healthy registered profile ID: native-ci-second\n"
        b"UR-BALDOSA-RECOVERY-COMMITTED: selected\n"
        b"UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-second\n"
        b"first frame simulated\n")
    files["interactive-S.key.log"] = b"exit=0\r\n\r\n"
    for i in (1, 2):
        files[f"cold-S-{i}.log"] = (
            b"UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-second\n"
            b"first frame simulated\n")
    return files, cmd


class TestOriginalS(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "original.zip"
        self.data, self.cmd = make_fixture()

    def pack(self, data):
        with zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, value in data.items():
                z.writestr(name, value)
        return sha(self.path.read_bytes())

    def test_positive_synthetic_contract_zero_gate(self):
        external = self.pack(self.data)
        report = qa.check_original_zip(self.path, external, self.cmd)
        self.assertEqual(report["rehashed_original_binary_members"], 29)
        self.assertEqual(report["sole_mutated_canonical_file"],
                         "host-state-v1.txt")
        self.assertEqual(report["release_gate_credit"], 0)
        self.assertFalse(report["human_operator_tested"])

    def test_tampering_and_missingness_fail_closed(self):
        mutations = {
            "altered damaged A": ("source-bytes/after-S.a-raw.bin", b"X" * 8192),
            "altered healthy B": ("source-bytes/cold1-S.b-raw.bin", b"Z" * 8192),
            "invented C typed": ("source-bytes/unrelated-C-original-typed.bin", b"bad"),
            "catalog modified": ("source-bytes/after-S.catalog.bin", b"wrong"),
            "no selector switch": ("source-bytes/after-S.selector.bin",
                                   self.data["source-bytes/before-S.selector.bin"]),
            "inj failed": ("interactive-S.key.log", b"exit=1\n"),
            "wrong choice": ("interactive-S.log", b"Q"),
            "missing cold": ("cold-S-2.log", None),
            "unreviewed personal ROM": ("Uniracers_USA.sfc", b"ROM"),
        }
        for name, (member, value) in mutations.items():
            with self.subTest(name=name):
                damaged = dict(self.data)
                if value is None:
                    damaged.pop(member)
                else:
                    damaged[member] = value
                with self.assertRaises(ValueError):
                    qa.check_original_zip(self.path, self.pack(damaged), self.cmd)

    def test_wrong_external_sha_rejected(self):
        real = self.pack(self.data)
        with self.assertRaises(ValueError):
            qa.check_original_zip(self.path, "f" * 64, self.cmd)
        with self.assertRaises(ValueError):
            qa.check_original_zip(self.path, real, "e" * 64)


if __name__ == "__main__":
    unittest.main()
