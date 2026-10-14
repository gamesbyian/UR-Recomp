#!/usr/bin/env python3
"""Independently compare CI-only, original-guest-earned paired Records snapshots.

Two *separately downloaded* Windows Actions artifacts are required:
(1) the small pre-Records pair-only ZIP uploaded by the Modern producer, and
(2) the existing source+six-game+raw-post-Records ZIP. Verify the latter using
the already independent raw consumer before considering the pre-view bytes.

A matching pair does NOT prove the stage's acquisition time or that the ZIPs
were downloaded from the same Actions run. Those require independent Actions
metadata and source step-order review. No original-emulator or release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from check_baldosa_win32_created_pair_raw_qa import (
    audit_zip as audit_post_source,
    RAW_PREFIX, MAX_ZIP,
    _read as read_post_member,
    sha256,
)
from check_baldosa_native_ci_pair_bytes_qa import MAX_RUN_BYTES, MAX_MATCH_BYTES

HEX = re.compile(r"[0-9a-f]{64}\Z")
PRE_SCHEMA = "baldosa-native-pre-records-pair-v1"
PRE_STAGE = "after-real-play-before-first-records-viewer"
PRE_SCOPE = "one-throwaway-Windows-CI-user-only"
PRE_MEMBER_LIMIT = 2 * MAX_RUN_BYTES + MAX_MATCH_BYTES + 128 * 1024


def require(value: bool, why: str) -> None:
    if not value:
        raise ValueError("Windows pair pre/post independent QA: " + why)


def _safe_read(z: zipfile.ZipFile, name: str, cap: int) -> bytes:
    info = z.getinfo(name)
    mode = (info.external_attr >> 16) & 0o170000
    require(not info.is_dir() and mode != 0o120000 and
            0 < info.file_size <= cap,
            "linked, empty, oversized or directory source member")
    data = z.read(info)
    require(len(data) == info.file_size, "incomplete source member")
    return data


def audit_pair(before: Path, after: Path, *,
               expected_before_sha256: str, expected_after_sha256: str) -> dict:
    """Fail closed on identities, allowlists, source, checksums and exact bytes."""
    require(all(type(v) is str and HEX.fullmatch(v) for v in (
                expected_before_sha256, expected_after_sha256)),
            "missing exact expected Actions artifact SHA-256")
    require(before.is_file() and after.is_file() and
            not before.is_symlink() and not after.is_symlink() and
            0 < before.stat().st_size <= MAX_ZIP and
            0 < after.stat().st_size <= MAX_ZIP,
            "nonexistent, linked or oversized exact evidence ZIP")
    require(sha256(before.read_bytes()) == expected_before_sha256 and
            sha256(after.read_bytes()) == expected_after_sha256,
            "Actions archive SHA-256 does not match independent expected identity")
    # This parser decodes all six genuine native UI/process logs and the raw
    # saved pair, rider SRAM, typed profiles, catalog and 2P source results.
    source = audit_post_source(after)
    run = source["run_basename"]
    pair = ("multiplayer-runs/" + run, "multiplayer-runs/" + run + ".urmatch")
    expected = {"manifest.json", *pair}
    with zipfile.ZipFile(before) as pre, zipfile.ZipFile(after) as post:
        names = pre.namelist()
        require(len(names) == len(expected) and
                len(names) == len(set(names)) and set(names) == expected,
                "pre-Records Actions ZIP has missing, duplicate or unreviewed members")
        raw_manifest = _safe_read(pre, "manifest.json", 64 * 1024)
        try:
            manifest = json.loads(raw_manifest.decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise ValueError("pre-Records CI manifest is not valid UTF-8 JSON") from exc
        require(type(manifest) is dict and set(manifest) == {
                    "schema", "stage", "scope", "source_profiles",
                    "source_pair", "members", "includes_rom",
                    "includes_executable", "release_gate_credit"
                } and manifest["schema"] == PRE_SCHEMA and
                manifest["stage"] == PRE_STAGE and
                manifest["scope"] == PRE_SCOPE and
                manifest["source_profiles"] == ["mike", "martin"] and
                manifest["source_pair"] == [run, run + ".urmatch"] and
                manifest["includes_rom"] is False and
                manifest["includes_executable"] is False and
                type(manifest["release_gate_credit"]) is int and
                manifest["release_gate_credit"] == 0 and
                type(manifest["members"]) is dict and
                set(manifest["members"]) == set(pair),
                "pre-Records producer manifest schema, scope or pair is untrusted")
        for name in pair:
            actual_before = _safe_read(
                pre, name, MAX_RUN_BYTES if name.endswith(".urrun") else MAX_MATCH_BYTES)
            claim = manifest["members"][name]
            require(type(claim) is dict and set(claim) == {"sha256", "bytes"} and
                    type(claim["bytes"]) is int and claim["bytes"] == len(actual_before)
                    and type(claim["sha256"]) is str and
                    HEX.fullmatch(claim["sha256"]) is not None and
                    sha256(actual_before) == claim["sha256"],
                    "pre-view stored member differs from producer manifest")
            actual_after = read_post_member(
                post, RAW_PREFIX + name,
                MAX_RUN_BYTES if name.endswith(".urrun") else MAX_MATCH_BYTES)
            require(actual_before == actual_after,
                    "genuine run or sidecar bytes differ across Records viewers")
        require(source["release_gate_credit"] == 0 and
                source["pair_bytes_seen_both_before_and_after_records_independently"]
                is False,
                "unexpected source release or snapshot-completeness assertion")
    return {
        "scope": "independently-compared-two-archived-source-pair-snapshots",
        "exact_before_actions_zip_sha256": expected_before_sha256,
        "exact_after_actions_zip_sha256": expected_after_sha256,
        "saved_pair_basename": run,
        "run_sha256": source["run_sha256_independently_rehashed"],
        "match_sha256": source["match_sha256_independently_rehashed"],
        "independently_compared_archived_run_and_sidecar_bytes_equal": True,
        "source_scored_winner": source["source_scored_winner"],
        "source_hundredths": source["source_hundredths"],
        "source_six_actual_native_processes_and_raw_pair_decoded": True,
        "source_stage_before_first_records_independently_timestamped": False,
        "same_GitHub_Actions_run_provenance_independently_verified": False,
        "physical_two_gamepads_and_live_audio_verified": False,
        "original_Snes9x_USA_complete_event_parity_proven": False,
        "final_merged_main_Windows_release_candidate_nominated": False,
        "release_gate_credit": 0,
        "outcome": "bounded_source_byte_snapshot_equality_only",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--before-zip", type=Path, required=True)
    p.add_argument("--after-zip", type=Path, required=True)
    p.add_argument("--expected-before-sha256", required=True)
    p.add_argument("--expected-after-sha256", required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = audit_pair(
        args.before_zip, args.after_zip,
        expected_before_sha256=args.expected_before_sha256,
        expected_after_sha256=args.expected_after_sha256)
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as output:
            output.write(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
