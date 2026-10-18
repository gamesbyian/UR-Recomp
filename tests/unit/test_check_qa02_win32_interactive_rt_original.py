#!/usr/bin/env python3
"""Synthetic ROM-free negative contracts; not genuine Windows repair evidence."""
from __future__ import annotations
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[2] / "tools/check_qa02_win32_interactive_rt_original.py"
spec = importlib.util.spec_from_file_location("qa02rt", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
def sha(data): return hashlib.sha256(data).hexdigest()


def source():
    cmd = sha(b"original cmd")
    committed = b"ASJIver3.30" + bytes(8192-11)
    raw = bytearray(committed)
    raw[256] ^= 1
    raw = bytes(raw)
    typed = (b"UR-HOST-PROFILE/5\nprofile=native-ci-rider\ngeneration=1\nstock_sram=" +
             committed.hex().encode() + b"\n")
    typed_r = (b"UR-HOST-PROFILE/5\nprofile=native-ci-rider\ngeneration=2\nstock_sram=" +
               raw.hex().encode() + b"\n")
    files, results = {}, {}
    for choice in ("R", "T"):
        before = {"catalog":b"catalog", "selector":b"selector",
                  "raw":raw, "typed":typed}
        after = {**before, "raw":raw if choice=="R" else committed,
                 "typed":typed_r if choice=="R" else typed}
        receipts = {}
        for stage, states in (("before",before),("after",after),
                              ("cold1",after),("cold2",after)):
            for label, data in states.items():
                name = f"{stage}-{choice}.{label}.bin"
                files[f"{choice}/source-bytes/{name}"] = data
                receipts[name] = {"bytes":len(data), "sha256":sha(data)}
        archive = (b"UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n"+
                   str(len(typed)).encode()+b"\n1\n8192\n"+typed+raw)
        name = f"manual-{choice}.bin"
        files[f"{choice}/source-bytes/{name}"] = archive
        receipts[name] = {"bytes":len(archive), "sha256":sha(archive)}
        files[f"{choice}/fixture.log"] = b"UR_BALDOSA_NATIVE_PROFILE_FIXTURE sram=8192\n"
        files[f"{choice}/interactive-{choice}.log"] = (
            f"UR-BALDOSA-STARTUP-PROFILE-REJECTED: data\n"
            f"Explicit recovery choice [R/T/S/Q]: {choice}\n"
            f"UR-BALDOSA-RECOVERY-COMMITTED: yes\n"
            f"first frame simulated\n").encode()
        files[f"{choice}/interactive-{choice}.key.log"] = b"exit=0\r\n"
        for cold in (1,2):
            files[f"{choice}/cold-{choice}-{cold}.log"] = b"first frame simulated\n"
        child = {"schema":"ur-win32-interactive-original-cmd-rt/1",
                 "choice":choice, "exact_extracted_cmd_sha256":cmd,
                 "actual_console_key_injected":True,
                 "original_cmd_recovery_committed_once":True,
                 "original_first_frame_after_relaunch":True,
                 "original_first_frame_on_two_cold_boots":True,
                 "source_before_after_and_cold_bytes":receipts,
                 "legacy_raw_byte_changes":1,
                 "manual_archive_exact_previous_raw_and_typed":True,
                 "unchanged_catalog_and_selector":True,
                 "independent_release_gate_credit":0}
        results[choice] = child
        files[f"{choice}/result.json"] = json.dumps(child, sort_keys=True, indent=2).encode()
    parent = {"schema":"ur-win32-interactive-original-cmd-rt/1",
              "tested_choices":["R","T"], "results":results,
              "physical_operator":False, "release_gate_credit":0}
    files["interactive-rt-result.json"] = json.dumps(
        parent, sort_keys=True, indent=2).encode()
    return files, cmd


class TestOriginalRT(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/"original.zip"
        self.files, self.cmd = source()

    def pack(self, files):
        with zipfile.ZipFile(self.path,"w",zipfile.ZIP_DEFLATED) as z:
            for name,data in files.items(): z.writestr(name,data)
        return sha(self.path.read_bytes())

    def test_rom_free_synthetic_positive_contract_has_zero_gate(self):
        receipt = mod.audit(self.path,self.pack(self.files),self.cmd)
        self.assertEqual(receipt["original_binary_members_independently_checked"],34)
        self.assertEqual(receipt["release_gate_credit"],0)
        self.assertFalse(receipt["physical_operator_verified"])

    def test_mutated_original_bytes_archive_and_console_rejected(self):
        mutations = {
            "T damaged archive":("T/source-bytes/manual-T.bin",b"x"),
            "R wrong raw":("R/source-bytes/after-R.raw.bin",b"z"*8192),
            "T wrong typed":("T/source-bytes/after-T.typed.bin",b"bad"),
            "R cold drift":("R/source-bytes/cold2-R.raw.bin",b"z"*8192),
            "T injector failed":("T/interactive-T.key.log",b"exit=1\n"),
            "R wrong choice":("R/interactive-R.log",b"Q"),
            "extra bundled ROM":("game.sfc",b"ROM"),
        }
        for label, (path, data) in mutations.items():
            with self.subTest(case=label):
                files = dict(self.files)
                files[path] = data
                with self.assertRaises(ValueError):
                    mod.audit(self.path,self.pack(files),self.cmd)

    def test_external_original_zip_and_cmd_pins_rejected(self):
        original = self.pack(self.files)
        with self.assertRaises(ValueError):
            mod.audit(self.path,"f"*64,self.cmd)
        with self.assertRaises(ValueError):
            mod.audit(self.path,original,"e"*64)


if __name__ == "__main__":
    unittest.main()
