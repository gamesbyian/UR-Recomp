#!/usr/bin/env python3
"""Independent ROM-free owner-download identity check; grants zero QA gates.

The producer verifies the Windows tested executable before export. This consumer
checks the separately downloaded four-file Actions artifact against EXTERNAL
source, wrapper, ZIP and executable digests. It cannot observe game runtime,
prove the workflow was on main, or certify any physical Windows device.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import tempfile
import zipfile
from pathlib import Path

import audit_baldosa_romless_candidate as inner_audit
import verify_baldosa_playtest_release as producer
from assemble_baldosa_windows_candidate import EXE, PREFIX
from check_windows_portable_binary import check_pe_x64

FILES = {producer.ZIP, producer.SIDECAR, "PLAYTEST-PROVENANCE.json", "RELEASE-NOTES.md"}
METADATA = {
    "schema", "source_commit", "zip_sha256", "tested_and_packaged_executable_sha256",
    "fixture_sha256", "github_release_tag", "accepted_original_native_complete_events",
    "independent_release_gates_accepted", "physical_gamepad_or_audio_verified",
    "release_gate_credit", "candidate_only", "not_a_certified_beta",
}
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
MAX_WRAPPER = inner_audit.MAX_ZIP_BYTES + 1024 * 1024


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("OWNER_DOWNLOAD_QA_REJECTED: " + reason)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def audit_download(*, artifact: Path, expected_source: str,
                   expected_wrapper: str, expected_zip: str,
                   expected_executable: str) -> dict:
    require(SHA40.fullmatch(expected_source) is not None, "invalid external source pin")
    for label, value in (("artifact", expected_wrapper), ("ZIP", expected_zip),
                         ("executable", expected_executable)):
        require(SHA64.fullmatch(value) is not None, "invalid external " + label + " digest")
    require(artifact.is_file() and not artifact.is_symlink(), "missing/redirected artifact")
    require(0 < artifact.stat().st_size <= MAX_WRAPPER, "artifact exceeds size budget")
    require(digest(artifact) == expected_wrapper, "download differs from independent Actions digest")
    with tempfile.TemporaryDirectory(prefix="ur-owner-qa-") as tmp:
        candidate = Path(tmp) / producer.ZIP
        executable = Path(tmp) / EXE
        with zipfile.ZipFile(artifact) as z:
            members = z.infolist()
            require(len(members) == 4 and {m.filename for m in members} == FILES,
                    "owner-download member population differs")
            for m in members:
                file_type = stat.S_IFMT(m.external_attr >> 16)
                require(not m.is_dir() and not (m.flag_bits & 1)
                        and file_type in (0, stat.S_IFREG),
                        "unsafe ZIP member or symlink: " + m.filename)
                max_bytes = inner_audit.MAX_ZIP_BYTES if m.filename == producer.ZIP else 32 * 1024
                require(0 < m.file_size <= max_bytes, "oversized/empty owner member")
            sidecar = z.read(producer.SIDECAR).decode("ascii")
            require(sidecar in (
                expected_zip + "  " + producer.ZIP + "\n",
                expected_zip + " *" + producer.ZIP + "\n",
            ), "owner checksum digest, basename or format differs")
            raw_metadata = z.read("PLAYTEST-PROVENANCE.json")
            metadata = json.loads(raw_metadata.decode("utf-8"))
            require(isinstance(metadata, dict) and set(metadata) == METADATA,
                    "provenance schema differs")
            require(raw_metadata == (json.dumps(metadata, sort_keys=True, indent=2) + "\n").encode(),
                    "noncanonical provenance JSON")
            require(metadata["schema"] == "ur-windows-romfree-playtest-provenance/1" and
                    metadata["source_commit"] == expected_source and
                    metadata["zip_sha256"] == expected_zip and
                    metadata["tested_and_packaged_executable_sha256"] == expected_executable and
                    isinstance(metadata["fixture_sha256"], str) and
                    SHA64.fullmatch(metadata["fixture_sha256"]) is not None and
                    metadata["github_release_tag"] == "playtest-" + expected_source[:12],
                    "provenance/source/binary conflict")
            require(type(metadata["accepted_original_native_complete_events"]) is int and
                    metadata["accepted_original_native_complete_events"] == 0 and
                    type(metadata["independent_release_gates_accepted"]) is int and
                    metadata["independent_release_gates_accepted"] == 0 and
                    type(metadata["release_gate_credit"]) is int and
                    metadata["release_gate_credit"] == 0 and
                    metadata["physical_gamepad_or_audio_verified"] is False and
                    metadata["candidate_only"] is True and
                    metadata["not_a_certified_beta"] is True,
                    "provisional/independent acceptance boundary changed")
            with z.open(producer.ZIP) as stream, candidate.open("xb") as output:
                h = hashlib.sha256()
                size = 0
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    size += len(block)
                    require(size <= inner_audit.MAX_ZIP_BYTES, "decompressed candidate exceeds bound")
                    output.write(block)
                    h.update(block)
            require(h.hexdigest() == expected_zip, "real inner ZIP bytes differ")
        inner = inner_audit.inspect(candidate, expected_revision=expected_source,
                                    expected_zip_sha256=expected_zip)
        require(inner["exe_sha256"] == expected_executable and
                inner["all_immutable_members_verified"] is True and
                inner["rom_bundled"] is False and
                inner["profile_data_bundled"] is False,
                "inner ROM-free manifest or executable identity differs")
        with zipfile.ZipFile(candidate) as z, z.open(PREFIX + EXE) as stream, executable.open("xb") as output:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                output.write(block)
        require(digest(executable) == expected_executable, "extracted game executable differs")
        check_pe_x64(executable)
    return {
        "schema": "ur-independent-owner-playtest-download-qa/1",
        "source_commit": expected_source,
        "actions_artifact_sha256": expected_wrapper,
        "zip_sha256": expected_zip,
        "exe_sha256": expected_executable,
        "verified_rom_free_package_bytes": True,
        "verified_win32_gameplay_execution_here": False,
        "verified_source_is_merged_main_here": False,
        "verified_physical_hardware_here": False,
        "independent_release_witnesses": [],
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actions-artifact", type=Path, required=True)
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--expected-actions-sha256", required=True)
    parser.add_argument("--expected-zip-sha256", required=True)
    parser.add_argument("--expected-exe-sha256", required=True)
    args = parser.parse_args()
    try:
        report = audit_download(artifact=args.actions_artifact,
                                expected_source=args.expected_source,
                                expected_wrapper=args.expected_actions_sha256,
                                expected_zip=args.expected_zip_sha256,
                                expected_executable=args.expected_exe_sha256)
    except (ValueError, OSError, zipfile.BadZipFile, UnicodeError, json.JSONDecodeError) as error:
        parser.exit(1, str(error) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
