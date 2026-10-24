"""Adversarial consumer checks on a real-format ROM-free ZIP and owner wrapper."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import assemble_baldosa_windows_candidate as build
import check_baldosa_owner_playtest_download_qa as qa

SOURCE = "0123456789abcdef0123456789abcdef01234567"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scenario(root: Path, *, binary_mode: bool = False) -> tuple[Path, dict, dict]:
    exe = root / build.EXE
    image = bytearray(65537)
    image[:2] = b"MZ"
    struct.pack_into("<I", image, 0x3c, 128)
    image[128:132] = b"PE\x00\x00"
    struct.pack_into("<H", image, 132, 0x8664)
    # A positive synthetic PE must carry the executable-image COFF flag.
    struct.pack_into("<H", image, 150, 0x0002)
    struct.pack_into("<H", image, 152, 0x20b)
    exe.write_bytes(image)
    inner = root / "inner.zip"
    build.create_candidate(exe, inner, SOURCE)
    zhash = sha(inner.read_bytes())
    ehash = sha(exe.read_bytes())
    metadata = {
        "schema": "ur-windows-romfree-playtest-provenance/1",
        "source_commit": SOURCE,
        "zip_sha256": zhash,
        "tested_and_packaged_executable_sha256": ehash,
        "fixture_sha256": "3" * 64,
        "github_release_tag": "playtest-" + SOURCE[:12],
        "accepted_original_native_complete_events": 0,
        "independent_release_gates_accepted": 0,
        "physical_gamepad_or_audio_verified": False,
        "release_gate_credit": 0,
        "candidate_only": True,
        "not_a_certified_beta": True,
    }
    members = {
        qa.producer.ZIP: inner.read_bytes(),
        qa.producer.SIDECAR: (zhash + (" *" if binary_mode else "  ") + qa.producer.ZIP + "\n").encode(),
        "PLAYTEST-PROVENANCE.json": (json.dumps(metadata, sort_keys=True, indent=2) + "\n").encode(),
        "RELEASE-NOTES.md": b"Provisional technical playtest only\n",
    }
    return root / "actions.zip", members, {"source": SOURCE, "zip": zhash, "exe": ehash}


def write_wrapper(path: Path, members: dict[str, bytes]) -> str:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return sha(path.read_bytes())


def run(path: Path, pins: dict, wrapper_sha: str) -> dict:
    return qa.audit_download(artifact=path, expected_source=pins["source"],
                             expected_wrapper=wrapper_sha, expected_zip=pins["zip"],
                             expected_executable=pins["exe"])


class OwnerArtifactConsumerTest(unittest.TestCase):
    def test_both_exact_canonical_sha256sum_forms(self):
        for binary in (False, True):
            with self.subTest(binary_mode=binary), tempfile.TemporaryDirectory() as directory:
                path, members, pins = scenario(Path(directory), binary_mode=binary)
                proof = run(path, pins, write_wrapper(path, members))
                self.assertTrue(proof["verified_rom_free_package_bytes"])
                self.assertEqual(proof["release_gate_credit"], 0)
                self.assertFalse(proof["verified_win32_gameplay_execution_here"])
                self.assertFalse(proof["verified_source_is_merged_main_here"])
                self.assertEqual(proof["independent_release_witnesses"], [])

    def test_external_wrapper_source_zip_and_executable_pins_reject_substitutions(self):
        with tempfile.TemporaryDirectory() as directory:
            path, members, pins = scenario(Path(directory))
            correct = write_wrapper(path, members)
            for key, corrupted in (("source", "f" * 40), ("zip", "f" * 64),
                                   ("exe", "f" * 64)):
                with self.subTest(pin=key), self.assertRaises(ValueError):
                    run(path, {**pins, key: corrupted}, correct)
            with self.assertRaisesRegex(ValueError, "independent Actions digest"):
                run(path, pins, "f" * 64)

    def test_unexpected_member_checksum_malformed_or_false_gate_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path, original, pins = scenario(Path(directory), binary_mode=True)
            edits = []
            edits.append({**original, "private-save.srm": b"PRIVATE"})
            edits.append({**original, qa.producer.SIDECAR: (pins["zip"] + " *wrong.zip\n").encode()})
            edits.append({**original, qa.producer.SIDECAR: ("0" * 64 + " *" + qa.producer.ZIP + "\n").encode()})
            edits.append({**original, qa.producer.ZIP: b"invalid candidate bytes"})
            for field, value in (("release_gate_credit", 1),
                                 ("physical_gamepad_or_audio_verified", True),
                                 ("source_commit", "f" * 40),
                                 ("tested_and_packaged_executable_sha256", "f" * 64)):
                data = json.loads(original["PLAYTEST-PROVENANCE.json"])
                data[field] = value
                edits.append({**original, "PLAYTEST-PROVENANCE.json":
                              (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()})
            for index, members in enumerate(edits):
                with self.subTest(edit=index):
                    wrapper = write_wrapper(path, members)
                    with self.assertRaises((ValueError, zipfile.BadZipFile)):
                        run(path, pins, wrapper)

    def test_inner_manifest_and_executable_not_trusted_from_updated_outer_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, members, pins = scenario(root)
            replaced = b"MZ" + b"substituted-game" * 100
            pins["zip"] = sha(replaced)
            members[qa.producer.ZIP] = replaced
            members[qa.producer.SIDECAR] = (pins["zip"] + "  " + qa.producer.ZIP + "\n").encode()
            meta = json.loads(members["PLAYTEST-PROVENANCE.json"])
            meta["zip_sha256"] = pins["zip"]
            members["PLAYTEST-PROVENANCE.json"] = (json.dumps(meta, sort_keys=True, indent=2) + "\n").encode()
            with self.assertRaises((ValueError, zipfile.BadZipFile)):
                run(path, pins, write_wrapper(path, members))


if __name__ == "__main__":
    unittest.main()
