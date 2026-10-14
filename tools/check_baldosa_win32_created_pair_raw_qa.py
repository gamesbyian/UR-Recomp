#!/usr/bin/env python3
"""Independent raw saved MIKE/MARTIN run/match/profile inspection.

Consumes only the explicit disposable native Windows CI source group plus
strictly allowlisted raw CI-owned byte export in one Actions ZIP. Does not
execute the original USA ROM, prove replay parity, publish scores, alter
player files, or certify real USB gamepads/audio/release QA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from check_baldosa_win32_created_pair_records_qa import (
    audit as audit_created_pair,
    UI_FILES, PREFIX,
)
from check_baldosa_native_ci_pair_bytes_qa import (
    canonical_lines, RUN_KEYS, MATCH_KEYS, DECIMAL, UPPER_HEX_MASK,
    USA_ROM_SHA256, BALDOSA_COMPAT, MAX_RUN_BYTES, MAX_MATCH_BYTES,
)

RAW_PREFIX = PREFIX + "ci-owned-raw-artifacts/"
RUN_PATTERN = re.compile(r"multiplayer-runs/(run-[0-9]{16}-[0-9]{4}\.urrun)\Z")
FIXED = frozenset((
    "host-state-v1.txt", "profiles-v1.txt",
    "saves/profile-mike/host-profile.txt",
    "saves/profile-mike/save.srm",
    "saves/profile-martin/host-profile.txt",
    "saves/profile-martin/save.srm",
))
OPTIONAL_ANONYMOUS = "saves/save.srm"
MANIFEST = "manifest.json"
SOURCE_GROUP = tuple(PREFIX + part for part in UI_FILES)
HEX = re.compile(r"[a-f0-9]{64}\Z")
MAX_REPORT = 64 * 1024
MAX_LOG = 2 * 1024 * 1024
MAX_ZIP = 16 * 1024 * 1024


def require(test: bool, why: str) -> None:
    if not test:
        raise ValueError("real created-pair raw Windows QA: " + why)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def raw_name_contract(names: list[str]) -> tuple[str, frozenset[str]]:
    """Authorize only known fixed profile/selector files plus ONE generated pair."""
    require(len(names) == len(set(names)), "duplicate archive member")
    raw = {name[len(RAW_PREFIX):] for name in names if name.startswith(RAW_PREFIX)}
    require(MANIFEST in raw, "missing exact raw CI manifest")
    run_names = [match.group(1) for name in raw
                 if (match := RUN_PATTERN.fullmatch(name)) is not None]
    require(len(run_names) == 1, "missing/ambiguous canonical .urrun basename")
    run = run_names[0]
    required = FIXED | {MANIFEST, "multiplayer-runs/" + run,
                        "multiplayer-runs/" + run + ".urmatch"}
    permitted = required | {OPTIONAL_ANONYMOUS}
    require(required <= raw and raw <= permitted,
            "unallowlisted, redirected, or incomplete throwaway profile/pair export")
    return run, frozenset(RAW_PREFIX + name for name in raw)


def _read(archive: zipfile.ZipFile, name: str, limit: int) -> bytes:
    info = archive.getinfo(name)
    require(not info.is_dir() and 0 < info.file_size <= limit
            and (info.external_attr >> 16) & 0o170000 != 0o120000,
            "linked/empty/oversized CI-owned exported bytes")
    body = archive.read(info)
    require(len(body) == info.file_size, "short decompressed CI-owned source bytes")
    return body


def _key_value(lines: list[str], keys: tuple[str, ...]) -> dict[str, str]:
    require(len(lines) == len(keys), "missing/extra run or match fields")
    out = {}
    for key, line in zip(keys, lines):
        prefix = key + " "
        require(line.startswith(prefix) and len(line) > len(prefix),
                "noncanonical source saved record key: " + key)
        out[key] = line[len(prefix):]
    return out


def _typed_profile(raw: bytes, save: bytes, who: str, rider: int) -> int:
    require(len(save) == 8192 and save[0x748] == rider,
            "wrong saved original rider/8KiB raw profile for " + who)
    require(b"\r" not in raw and b"\0" not in raw and raw.endswith(b"\n"),
            "noncanonical typed player file")
    try:
        lines = raw.decode("ascii").splitlines()
        require(lines and lines[0] == "UR-HOST-PROFILE/5",
                "wrong typed player schema")
        fields = {}
        for line in lines[1:]:
            require("=" in line, "invalid typed profile key")
            key, value = line.split("=", 1)
            require(key not in fields, "duplicated typed profile authority")
            fields[key] = value
        require(fields.get("profile") == who and
                fields.get("racer_name") == who.upper() and
                fields.get("racer_index") == str(rider),
                "typed profile name/rider disagrees with catalog and raw SRAM")
        generation = int(fields.get("generation", ""))
        require(generation > 0, "nonpositive typed generation")
        require(bytes.fromhex(fields["stock_sram"]) == save,
                "typed 8192-byte SRAM is not exact raw saved profile mirror")
    except (ValueError, KeyError, UnicodeError) as exc:
        raise ValueError("malformed independently decoded typed SRAM") from exc
    return generation


def audit_zip(path: Path) -> dict[str, object]:
    require(path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size <= MAX_ZIP,
            "Windows CI source artifact absent, linked or unbounded")
    with zipfile.ZipFile(path) as archive:
        all_names = archive.namelist()
        run_name, allowed_raw = raw_name_contract(all_names)
        # The raw-subtree allowlist alone cannot rule out unrelated source-root
        # files (including private saves or executables) in the same ZIP.
        # Evidence provenance and privacy require an exact WHOLE archive set.
        require(set(all_names) == set(SOURCE_GROUP) | set(allowed_raw),
                "unallowlisted Windows source ZIP member outside guest/raw group")
        require(all(name in all_names for name in SOURCE_GROUP),
                "missing six exact played/controller-selected native game logs")
        raw_manifest = _read(archive, RAW_PREFIX + MANIFEST, MAX_REPORT)
        try:
            manifest = json.loads(raw_manifest.decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise ValueError("raw CI manifest encoding invalid") from exc
        require(type(manifest) is dict and set(manifest) == {
            "schema", "scope", "includes_executable", "includes_rom",
            "release_gate_credit", "source_profiles", "source_pair", "members"
        } and manifest["schema"] == "baldosa-native-disposable-source-pair-v1"
                and manifest["scope"] == "one-throwaway-Windows-CI-user-only"
                and manifest["source_profiles"] == ["mike", "martin"]
                and manifest["source_pair"] == [run_name, run_name + ".urmatch"]
                and manifest["includes_rom"] is False
                and manifest["includes_executable"] is False
                and type(manifest["release_gate_credit"]) is int
                and manifest["release_gate_credit"] == 0,
                "producer raw source manifest claims unsafe export or unsupported release")
        claims = manifest["members"]
        expected = {name[len(RAW_PREFIX):] for name in allowed_raw} - {MANIFEST}
        require(type(claims) is dict and set(claims) == expected,
                "raw manifest has unreviewed/absent/extra source member")
        payload: dict[str, bytes] = {}
        for name in sorted(expected):
            described = claims[name]
            require(type(described) is dict and
                    set(described) == {"bytes", "sha256"} and
                    type(described["bytes"]) is int and described["bytes"] > 0
                    and type(described["sha256"]) is str
                    and HEX.fullmatch(described["sha256"]) is not None,
                    "raw manifest member metadata malformed")
            limit = (MAX_RUN_BYTES if name.endswith(".urrun") else
                     MAX_MATCH_BYTES if name.endswith(".urmatch") else
                     32 * 1024 if name.endswith(".txt") else 8192)
            if name.endswith("save.srm"):
                limit = 8192
            raw = _read(archive, RAW_PREFIX + name, limit)
            require(len(raw) == described["bytes"] and
                    sha256(raw) == described["sha256"],
                    "producer manifest hash/size does not match actual raw bytes")
            payload[name] = raw
        # Bind the original UI-created race, two fresh earned Records and the
        # real NEXT boot profile switch to exactly this same ZIP.
        source_raw = [_read(archive, member,
                            MAX_REPORT if i == 0 else MAX_LOG)
                      for i, member in enumerate(SOURCE_GROUP)]
        source = audit_created_pair(*source_raw)
        require(source["martin_selection_via_real_native_ui_controller_semantics"]
                is True and source["source_rider_pair"] == [0, 2] and
                source["release_gate_credit"] == 0,
                "source group did not independently establish one created UI pair")
        reported = source["reported_one_pair_digests"]
        require(set(reported) == {run_name, run_name + ".urmatch"} and
                reported[run_name] == claims["multiplayer-runs/" + run_name]["sha256"]
                and reported[run_name + ".urmatch"] ==
                claims["multiplayer-runs/" + run_name + ".urmatch"]["sha256"],
                "real source publisher pair hashes differ from retained raw bytes")
        p1 = "saves/profile-mike/"
        p2 = "saves/profile-martin/"
        g1 = _typed_profile(payload[p1 + "host-profile.txt"],
                            payload[p1 + "save.srm"], "mike", 0)
        g2 = _typed_profile(payload[p2 + "host-profile.txt"],
                            payload[p2 + "save.srm"], "martin", 2)
        require(payload["profiles-v1.txt"] ==
                b"UR-PROFILE-CATALOG/1\nmike|0|MIKE\nmartin|2|MARTIN\n",
                "final committed catalog does not contain only the two created riders")
        state = payload["host-state-v1.txt"]
        require(state.startswith(b"UR-HOST-STATE/6\n") and
                state.count(b"profile=martin\n") == 1 and
                b"profile=mike\n" not in state,
                "fresh MARTIN Records did not leave final selected profile")
        if OPTIONAL_ANONYMOUS in payload:
            require(len(payload[OPTIONAL_ANONYMOUS]) == 8192,
                    "anonymous source bootstrap SRAM is not 8192 bytes")
        run_bytes = payload["multiplayer-runs/" + run_name]
        match_bytes = payload["multiplayer-runs/" + run_name + ".urmatch"]
        run_rows, run_checksum = canonical_lines(run_bytes, MAX_RUN_BYTES)
        match_rows, match_checksum = canonical_lines(match_bytes, MAX_MATCH_BYTES)
        require(run_rows[0] == "URRUN 1" and
                run_rows[-2] == "END" and
                match_rows[0] == "UR-MULTIPLAYER-MATCH/1" and
                len(match_rows) == len(MATCH_KEYS) + 2,
                "raw run/match source schemas incorrect")
        rv = _key_value(run_rows[1:9], RUN_KEYS)
        cents = source["scored_source_hundredths"]
        expected_run = {
            "game": "uniracers-usa", "rom_sha256": USA_ROM_SHA256,
            "build_compat": BALDOSA_COMPAT,
            "course": "course:01", "mode": "race-2p",
            "elapsed_ticks60": str((min(cents) * 60 + 50) // 100),
            "frame_count": str(source["source_input_frames"]) if
                "source_input_frames" in source else str(
                    json.loads(source_raw[0])["observed_source_guest_result"]
                    ["source_input_frames"]),
            "terminal_digest": "-",
        }
        require(rv == expected_run, "raw saved run not bound to original scored source")
        input_rows = run_rows[9:-2]
        count = int(re.search(r"(?m)^UR_BALDOSA_NATIVE_RESULT observed=1 "
                              r".+ input_runs=(\d+) published=1\r?$",
                              source_raw[3].decode("utf-8")).group(1))
        require(len(input_rows) == count, "raw run input spans not source-observed")
        prior_end = 0
        prior_masks: tuple[int, int] | None = None
        p1_present = p2_present = False
        frames = int(rv["frame_count"])
        for row in input_rows:
            parts = row.split(" ")
            require(len(parts) == 5 and parts[0] == "input" and
                    all(DECIMAL.fullmatch(a) for a in parts[1:3]) and
                    all(UPPER_HEX_MASK.fullmatch(a) for a in parts[3:]),
                    "run has noncanonical source input masks")
            start, duration = int(parts[1]), int(parts[2])
            masks = (int(parts[3], 16), int(parts[4], 16))
            require(duration >= 1 and start >= prior_end and
                    start + duration <= frames and
                    masks != (0, 0) and max(masks) <= 0xfff and
                    not (start == prior_end and masks == prior_masks),
                    "run input frames out of range/overlapping/duplicate adjacent")
            prior_end = start + duration
            prior_masks = masks
            p1_present |= masks[0] != 0
            p2_present |= masks[1] != 0
        require(p1_present and p2_present, "newly created 2P run lacks one input lane")
        mv = _key_value(match_rows[1:-1], MATCH_KEYS)
        winner = source["scored_source_winner"]
        expected_match = {
            "run_checksum": run_checksum, "course": "course:01",
            "outcome": {0: "draw", 1: "p1", 2: "p2"}[winner],
            "p1_result": str(cents[0]), "p2_result": str(cents[1]),
            "p1_profile": "mike".encode().hex(),
            "p1_name": "MIKE".encode().hex(), "p1_rider": "0",
            "p2_profile": "martin".encode().hex(),
            "p2_name": "MARTIN".encode().hex(), "p2_rider": "2",
        }
        require(mv == expected_match,
                "raw .urmatch mismatches original source rider, participant, score or run hash")
    return {
        "scope": "actual-windows-native-created-players-one-scored-pair-raw-bytes",
        "artifact_sha256": sha256(path.read_bytes()),
        "ci_raw_manifest_sha256": sha256(raw_manifest),
        "run_basename": run_name,
        "run_sha256_independently_rehashed": sha256(run_bytes),
        "match_sha256_independently_rehashed": sha256(match_bytes),
        "run_internal_fnv64": run_checksum,
        "match_internal_fnv64": match_checksum,
        "rider_ids_from_independent_8192_byte_SRAM": [0, 2],
        "typed_profile_generations": {"mike": g1, "martin": g2},
        "typed_profiles_exactly_match_both_raw_SRAM": True,
        "selected_profile_final_state": "martin",
        "independently_decoded_source_input_frames": frames,
        "independently_decoded_source_input_runs": len(input_rows),
        "source_scored_winner": winner,
        "source_hundredths": cents,
        "fresh_MIKE_and_MARTIN_2p_Records_source_log_consistent": True,
        "pair_bytes_seen_both_before_and_after_records_independently": False,
        "original_Snes9x_USA_complete_event_parity_proven": False,
        "physical_two_gamepads_and_real_audio_verified": False,
        "release_gate_credit": 0,
        "outcome": "independent_real_source_guest_pair_and_profile_saved_byte_consistency_only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_zip(args.runtime)
    body = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(body, end="")
    else:
        with args.output.open("x", encoding="utf-8") as target:
            target.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
