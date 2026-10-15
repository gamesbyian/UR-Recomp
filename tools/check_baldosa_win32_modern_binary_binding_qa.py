#!/usr/bin/env python3
"""Bind genuine hosted Win32 Options/Practice source logs to the exact game EXE.

Independent, offline and read-only. Six original Windows Actions artifacts:
two evidence archives, two ROM-free candidate ZIP wrappers and two separate
tested-executable binding receipts. The source evidence consumer is reused.
This proves immutable Win32 source/package identity, never physical hardware,
power-loss durability, original/native complete-event parity or release QA gates.
"""
from __future__ import annotations

import argparse
import json
import re
import stat
import tempfile
import zipfile
from pathlib import Path

import audit_baldosa_romless_candidate as romless
import bind_baldosa_candidate_receipt as binder
import check_baldosa_win32_modern_repeatability_qa as source_reader
from assemble_baldosa_windows_candidate import EXE, PREFIX
from check_windows_portable_binary import check_pe_x64
from verify_baldosa_playtest_release import ZIP, SIDECAR

RECEIPT = source_reader.RECEIPT
MAX_WRAPPER = romless.MAX_ZIP_BYTES + 1048576


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("MODERN_WINDOWS_BINDING_QA_REJECTED: " + reason)


def inspect_wrapper(path: Path, expected_sha: str,
                    files: set[str]) -> dict[str, bytes]:
    require(bool(source_reader.SHA.fullmatch(expected_sha)),
            "missing independent Actions wrapper pin")
    require(path.is_file() and not path.is_symlink() and
            0 < path.stat().st_size <= MAX_WRAPPER,
            "missing/redirected or oversized wrapper")
    require(binder.sha256_file(path) == expected_sha,
            "actual Actions archive SHA256 differs from independent pin")
    contents = {}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        require(len(infos) == len(files) and
                {item.filename for item in infos} == files,
                "missing, duplicate or extra candidate/binding member")
        require(sum(item.file_size for item in infos) <= romless.MAX_ZIP_BYTES + 65536,
                "decompressed outer member bytes exceed bound")
        for info in infos:
            mode = stat.S_IFMT(info.external_attr >> 16)
            limit = romless.MAX_ZIP_BYTES if info.filename == ZIP else 65536
            require(not info.is_dir() and not (info.flag_bits & 1) and
                    mode in (0, stat.S_IFREG) and
                    0 < info.file_size <= limit,
                    "unsafe, encrypted, empty or oversized ZIP member")
            contents[info.filename] = archive.read(info)
            require(len(contents[info.filename]) == info.file_size,
                    "outer member size mismatch")
    return contents


def audit_package(candidate_wrapper: Path, binding_wrapper: Path,
                  run: dict) -> dict:
    source = run["source_sha"]
    expected_zip = run["candidate_inner_zip_sha256"]
    expected_exe = run["packaged_executable_sha256"]
    require(bool(source_reader.SOURCE.fullmatch(source)) and
            all(source_reader.SHA.fullmatch(v) for v in (expected_zip, expected_exe)),
            "missing source or exact inner package pins")
    package = inspect_wrapper(
        candidate_wrapper, run["candidate_wrapper"]["sha256"], {ZIP, SIDECAR})
    binding = inspect_wrapper(
        binding_wrapper, run["binding_wrapper"]["sha256"], {"candidate-binding.json"})
    require(package[SIDECAR] in (
        (expected_zip + "  " + ZIP + "\n").encode("ascii"),
        (expected_zip + " *" + ZIP + "\n").encode("ascii"),
    ), "noncanonical or wrong Windows package SHA256SUM sidecar")

    with tempfile.TemporaryDirectory(prefix="ur-win32-source-bind-") as root:
        directory = Path(root)
        candidate = directory / ZIP
        sidecar = directory / SIDECAR
        exe = directory / EXE
        candidate.write_bytes(package[ZIP])
        sidecar.write_bytes(package[SIDECAR])
        inner = romless.inspect(candidate, expected_revision=source,
                                expected_zip_sha256=expected_zip)
        require(inner["exe_sha256"] == expected_exe and
                inner["all_immutable_members_verified"] is True and
                inner["rom_bundled"] is False and
                inner["profile_data_bundled"] is False,
                "independent immutable Windows executable mismatch")
        with zipfile.ZipFile(candidate) as zipped, exe.open("xb") as out:
            info = zipped.getinfo(PREFIX + EXE)
            require(info.file_size <= romless.MAX_EXE_BYTES,
                    "unbounded executable byte count")
            with zipped.open(info) as stream:
                for chunk in iter(lambda: stream.read(1048576), b""):
                    out.write(chunk)
        check_pe_x64(exe)
        require(binder.sha256_file(exe) == expected_exe,
                "extracted Windows PE32+ bytes differ")
        authoritative = binder.bind(exe, candidate, sidecar, source)

        raw_receipt = binding["candidate-binding.json"]
        receipt = json.loads(raw_receipt.decode("utf-8"))
        require(type(receipt) is dict and
                raw_receipt == (json.dumps(receipt, sort_keys=True, indent=2) +
                                "\n").encode("utf-8") and
                receipt == authoritative,
                "tested Windows executable binding differs from actual package")

    return {
        "workflow_run_id": run["workflow_run_id"],
        "source_revision": source,
        "actions_candidate_wrapper_sha256": run["candidate_wrapper"]["sha256"],
        "actions_binding_wrapper_sha256": run["binding_wrapper"]["sha256"],
        "portable_zip_sha256": expected_zip,
        "executable_sha256": expected_exe,
        "physical_hardware_witness": False,
        "real_process_to_executable_cryptographic_identity": True,
        "release_gate_credit": 0,
    }


def audit(earlier_source: Path, later_source: Path, earlier_candidate: Path,
          later_candidate: Path, earlier_binding: Path, later_binding: Path,
          receipt: Path = RECEIPT) -> dict:
    native = source_reader.audit(earlier_source, later_source, receipt)
    document = json.loads(receipt.read_text(encoding="utf-8"))
    require(len(document["runs"]) == len(native["runs"]) == 2,
            "unexpected documented Win32 run population")
    packaged = [
        audit_package(candidate, binding, run)
        for candidate, binding, run in zip(
            (earlier_candidate, later_candidate),
            (earlier_binding, later_binding), document["runs"])
    ]
    require([entry["workflow_run_id"] for entry in packaged] ==
            [entry["workflow_run_id"] for entry in native["runs"]],
            "runtime and candidate workflows are not same-run bound")
    return {
        "schema": "ur-independent-actual-win32-modern-source-package-binding/1",
        "source_events_each_run": 1358,
        "genuine_native_processes_each_run": 15,
        "runs": packaged,
        "original_artifacts_rehashed": 6,
        "actual_different_executable_revisions": (
            packaged[0]["executable_sha256"] != packaged[1]["executable_sha256"]),
        "exact_main_release_candidate_verified": False,
        "physical_gamepad_audio_display_verified": False,
        "original_native_complete_events_accepted": 0,
        "release_gates_accepted": 0,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("earlier-source", "later-source", "earlier-candidate",
                 "later-candidate", "earlier-binding", "later-binding"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--receipt", type=Path, default=RECEIPT)
    args = parser.parse_args()
    try:
        result = audit(args.earlier_source, args.later_source,
                       args.earlier_candidate, args.later_candidate,
                       args.earlier_binding, args.later_binding, args.receipt)
    except (ValueError, KeyError, OSError, zipfile.BadZipFile,
            UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(1, str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
