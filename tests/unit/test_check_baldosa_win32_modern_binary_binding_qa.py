"""Fail-closed offline Windows package-to-source binding tests. Synthetic PE bytes only."""
from __future__ import annotations

import hashlib
import json
import stat
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import assemble_baldosa_windows_candidate as build
import bind_baldosa_candidate_receipt as binder
import check_baldosa_win32_modern_binary_binding_qa as qa


SOURCE = "abcdef0123456789abcdef0123456789abcdef01"


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def zip_bytes(payloads: dict[str, bytes]) -> bytes:
    import io
    out = io.BytesIO()
    with zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in payloads.items():
            z.writestr(name, data)
    return out.getvalue()


def scenario(root: Path, *, binary_sidecar: bool = False):
    exe = root / build.EXE
    pe = bytearray(65537)
    pe[:2] = b"MZ"
    struct.pack_into("<I", pe, 0x3c, 128)
    pe[128:132] = b"PE\x00\x00"
    struct.pack_into("<H", pe, 132, 0x8664)
    # A positive synthetic PE must carry the executable-image COFF flag.
    struct.pack_into("<H", pe, 148, 2)  # SizeOfOptionalHeader includes PE32+ magic
    struct.pack_into("<H", pe, 150, 0x0002)
    struct.pack_into("<H", pe, 152, 0x20b)
    exe.write_bytes(pe)
    candidate = root / qa.ZIP
    build.create_candidate(exe, candidate, SOURCE)
    candidate_sha = binder.sha256_file(candidate)
    sidecar = root / qa.SIDECAR
    sidecar.write_text(candidate_sha + (" *" if binary_sidecar else "  ") + qa.ZIP + "\n")
    receipt = binder.bind(exe, candidate, sidecar, SOURCE)
    canonical = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    artifacts = {
        "candidate": zip_bytes({qa.ZIP: candidate.read_bytes(), qa.SIDECAR: sidecar.read_bytes()}),
        "binding": zip_bytes({"candidate-binding.json": canonical}),
    }
    paths = {}
    for name, blob in artifacts.items():
        paths[name] = root / (name + "-artifact.zip")
        paths[name].write_bytes(blob)
    expected = {
        "workflow_run_id": 38701860728,
        "source_sha": SOURCE,
        "candidate_inner_zip_sha256": candidate_sha,
        "packaged_executable_sha256": sha(bytes(pe)),
        "candidate_wrapper": {"sha256": sha(artifacts["candidate"])},
        "binding_wrapper": {"sha256": sha(artifacts["binding"])},
    }
    return paths, expected


class IndependentWin32BinaryBindingTests(unittest.TestCase):
    def test_actual_synthetic_pe_bytes_and_both_gnu_sidecar_encodings(self):
        for binary in (False, True):
            with self.subTest(binary=binary), tempfile.TemporaryDirectory() as d:
                artifacts, expected = scenario(Path(d), binary_sidecar=binary)
                proof = qa.audit_package(artifacts["candidate"], artifacts["binding"], expected)
                self.assertTrue(proof["real_process_to_executable_cryptographic_identity"])
                self.assertFalse(proof["physical_hardware_witness"])
                self.assertEqual(proof["release_gate_credit"], 0)

    def test_real_win32_crlf_and_posix_lf_canonical_receipts_only(self):
        # The original real native Windows Actions binding receipts from
        # #1648 runs 38701860728, 38703695304 and 38786867862 all use CRLF.
        # Re-sign the outer wrapper for every variant, so rejection cannot
        # be attributed merely to the external wrapper SHA256.
        with tempfile.TemporaryDirectory() as d:
            paths, expected = scenario(Path(d))
            with zipfile.ZipFile(paths["binding"]) as z:
                lf = z.read("candidate-binding.json")
            crlf = lf.replace(b"\n", b"\r\n")
            cases = (
                ("posix-lf", lf, True),
                ("windows-crlf", crlf, True),
                ("mixed-line-endings", crlf.replace(b"\r\n", b"\n", 1), False),
                ("extra-trailing-line", lf + b"\n", False),
                ("changed-indentation", lf.replace(b'  "claims"', b' "claims"'), False),
            )
            for label, raw, accepted in cases:
                with self.subTest(case=label):
                    wrapped = zip_bytes({"candidate-binding.json": raw})
                    paths["binding"].write_bytes(wrapped)
                    expected["binding_wrapper"]["sha256"] = sha(wrapped)
                    if accepted:
                        proof = qa.audit_package(paths["candidate"],
                                                 paths["binding"], expected)
                        self.assertTrue(proof["real_process_to_executable_cryptographic_identity"])
                    else:
                        with self.assertRaisesRegex(ValueError, "binding differs"):
                            qa.audit_package(paths["candidate"],
                                             paths["binding"], expected)

    def test_wrong_source_zip_exe_and_wrapper_pins_refused(self):
        with tempfile.TemporaryDirectory() as d:
            paths, original = scenario(Path(d))
            mutations = [
                {**original, "source_sha": "f" * 40},
                {**original, "candidate_inner_zip_sha256": "f" * 64},
                {**original, "packaged_executable_sha256": "f" * 64},
                {**original, "candidate_wrapper": {"sha256": "f" * 64}},
                {**original, "binding_wrapper": {"sha256": "f" * 64}},
            ]
            for i, changed in enumerate(mutations):
                with self.subTest(pin=i), self.assertRaises(ValueError):
                    qa.audit_package(paths["candidate"], paths["binding"], changed)

    def test_forged_binding_receipt_rejected_even_if_outer_hash_updated(self):
        with tempfile.TemporaryDirectory() as d:
            paths, expected = scenario(Path(d))
            with zipfile.ZipFile(paths["binding"]) as z:
                receipt = json.loads(z.read("candidate-binding.json"))
            receipt["executable_bytes"] += 1
            mutated = zip_bytes({
                "candidate-binding.json": (json.dumps(receipt, sort_keys=True, indent=2)
                                           + "\n").encode()})
            paths["binding"].write_bytes(mutated)
            expected["binding_wrapper"]["sha256"] = sha(mutated)
            with self.assertRaisesRegex(ValueError, "binding differs"):
                qa.audit_package(paths["candidate"], paths["binding"], expected)

    def test_noncanonical_sha_or_private_extra_member_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            paths, expected = scenario(Path(d))
            with zipfile.ZipFile(paths["candidate"]) as z:
                original = {x.filename: z.read(x) for x in z.infolist()}
            for changed in (
                {**original, qa.SIDECAR: b"false digest"},
                {**original, "private-profile.srm": b"NEVER"},
                {**original, qa.ZIP: b"MZ+faked substituted ZIP"},
            ):
                with self.subTest(change=tuple(changed)), tempfile.TemporaryDirectory() as _:
                    payload = zip_bytes(changed)
                    paths["candidate"].write_bytes(payload)
                    expected["candidate_wrapper"]["sha256"] = sha(payload)
                    with self.assertRaises((ValueError, zipfile.BadZipFile)):
                        qa.audit_package(paths["candidate"], paths["binding"], expected)

    def test_binding_archive_symlink_is_not_a_document(self):
        with tempfile.TemporaryDirectory() as d:
            paths, expected = scenario(Path(d))
            import io
            out = io.BytesIO()
            with zipfile.ZipFile(out, "w") as z:
                item = zipfile.ZipInfo("candidate-binding.json")
                item.create_system = 3
                item.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(item, "../secret")
            paths["binding"].write_bytes(out.getvalue())
            expected["binding_wrapper"]["sha256"] = sha(out.getvalue())
            with self.assertRaisesRegex(ValueError, "unsafe"):
                qa.audit_package(paths["candidate"], paths["binding"], expected)


if __name__ == "__main__":
    unittest.main()
