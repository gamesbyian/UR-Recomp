#!/usr/bin/env python3
"""Fail-closed verifier for retention of one historically nominated owner ZIP.

This extends downloadability only. It never nominates another executable,
reclassifies independent release QA, or publishes a GitHub release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import audit_baldosa_romless_candidate as candidate_audit

SOURCE_COMMIT = "11501a15dea38fa912335cfc63103ce3a7208001"
CANDIDATE_SHA256 = "5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7"
EXE_SHA256 = "0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9"
ORIGINAL_RUN = 38813101482
ORIGINAL_ARTIFACT = 12009612842
ZIP = "UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip"
NAMES = {ZIP, ZIP + ".sha256", "PLAYTEST-PROVENANCE.json", "RELEASE-NOTES.md"}


def require(value: bool, why: str) -> None:
    if not value:
        raise ValueError("OWNER_RETENTION_INVALID: " + why)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for block in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate(root: Path) -> dict[str, object]:
    require(root.is_dir() and not root.is_symlink(), "root is not a plain directory")
    listed = list(root.iterdir())
    require({p.name for p in listed} == NAMES and len(listed) == len(NAMES),
            "exact original four-file owner artifact is required")
    require(all(p.is_file() and not p.is_symlink() for p in listed),
            "non-file or symlink encountered")
    files = {p.name: p for p in listed}
    sidecar = files[ZIP + ".sha256"].read_bytes()
    require(sidecar in (
        f"{CANDIDATE_SHA256}  {ZIP}\n".encode("ascii"),
        f"{CANDIDATE_SHA256} *{ZIP}\n".encode("ascii"),
    ), "candidate checksum sidecar changed")
    require(sha256(files[ZIP]) == CANDIDATE_SHA256,
            "inner ROM-free ZIP differs from nominated exact bytes")
    try:
        provenance = json.loads(files["PLAYTEST-PROVENANCE.json"].read_text("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("OWNER_RETENTION_INVALID: malformed provenance JSON") from exc
    require(isinstance(provenance, dict), "provenance must be an object")
    pinned = {
        "schema": "ur-windows-romfree-playtest-provenance/1",
        "source_commit": SOURCE_COMMIT,
        "zip_sha256": CANDIDATE_SHA256,
        "tested_and_packaged_executable_sha256": EXE_SHA256,
        "github_release_tag": "playtest-" + SOURCE_COMMIT[:12],
        "accepted_original_native_complete_events": 0,
        "independent_release_gates_accepted": 0,
        "physical_gamepad_or_audio_verified": False,
        "release_gate_credit": 0,
        "candidate_only": True,
        "not_a_certified_beta": True,
    }
    require(all(provenance.get(key) == value for key, value in pinned.items()),
            "candidate identity or noncertification flags changed")
    fixture = provenance.get("fixture_sha256")
    require(isinstance(fixture, str) and re.fullmatch(r"[0-9a-f]{64}", fixture) is not None,
            "fixture identity absent")
    # Reuse the existing strict candidate audit: immutable member SHA-256,
    # expected revision, structure, executable, ROM and save-data exclusions.
    result = candidate_audit.inspect(files[ZIP], expected_revision=SOURCE_COMMIT,
                                     expected_zip_sha256=CANDIDATE_SHA256)
    require(result["all_immutable_members_verified"] is True and
            result["rom_bundled"] is False and
            result["profile_data_bundled"] is False and
            result["exe_sha256"] == EXE_SHA256,
            "embedded candidate does not match existing ROM-free approval")
    notes = files["RELEASE-NOTES.md"].read_text("utf-8")
    require("provisional" in notes.lower() and SOURCE_COMMIT in notes and
            CANDIDATE_SHA256 in notes,
            "original cautionary release notes or hash pins changed")
    return {
        "schema": "ur-original-playtest-artifact-retention/1",
        "original_run_id": ORIGINAL_RUN,
        "original_artifact_id": ORIGINAL_ARTIFACT,
        "source_commit": SOURCE_COMMIT,
        "zip_sha256": CANDIDATE_SHA256,
        "exe_sha256": EXE_SHA256,
        "verified_original_four_file_names": sorted(NAMES),
        "release_gate_credit": 0,
        "new_candidate_nominated": False,
        "physical_hardware_verified": False,
        "github_release_created": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--receipt", required=True, type=Path)
    args = p.parse_args()
    receipt = validate(args.root)
    require(not args.receipt.exists() and not args.receipt.is_symlink(),
            "refusing to overwrite prior attestation")
    args.receipt.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
