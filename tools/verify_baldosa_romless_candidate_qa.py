#!/usr/bin/env python3
"""Independent, ROM-free admission for the provisional Baldosa Windows ZIP.

This reads a *prebuilt* four-member native candidate and requires the
reviewer's externally nominated full source SHA and actual ZIP digest.
It does not build, launch, download, extract ROM data, claim native 2P
Records acceptance, or authenticate the nomination itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import tempfile
import zipfile
from pathlib import Path

from assemble_baldosa_windows_candidate import (
    EXE, LAUNCHER, README, MANIFEST, ROM, USA_SHA256, PREFIX,
    ZIP_EPOCH, MAX_EXE_BYTES,
)
from evidence_contract import assertion, make_envelope
from check_baldosa_win32_native_1p_records_evidence import audit_hosted_native_1p_records
from check_baldosa_win32_native_2p_records_evidence import audit_hosted_native_2p_records
from check_baldosa_win32_first_racer_evidence import audit_hosted_win32_first_racer
from check_baldosa_win32_first_racer_earned_records_qa import audit_hosted_first_racer_earned_1p
from check_baldosa_win32_cmd_first_racer_evidence import audit_win32_cmd_first_racer_source
from check_baldosa_win32_second_racer_go_qa import audit_win32_second_created_racer_go
from check_baldosa_win32_product_groups_qa import (
    ALLOWED_MEMBERS as PRODUCT_SOURCE_MEMBERS,
    audit_extra_hosted_groups,
)

SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED = tuple(sorted((EXE, LAUNCHER, README, MANIFEST)))
PAYLOAD_NAMES = tuple(sorted((EXE, LAUNCHER, README)))
MAX_ZIP_BYTES = MAX_EXE_BYTES + 2 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024
MAX_LAUNCHER_BYTES = 32 * 1024
MAX_README_BYTES = 64 * 1024
BLOCK = 1 << 20
ACTIONS_INNER = "UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip"
ACTIONS_CHECKSUM = ACTIONS_INNER + ".sha256"


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(BLOCK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zip_member_digest(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest = hashlib.sha256()
    count = 0
    with archive.open(info) as stream:
        for chunk in iter(lambda: stream.read(BLOCK), b""):
            count += len(chunk)
            if count > info.file_size:
                raise ValueError("decompressed candidate payload exceeded advertised size")
            digest.update(chunk)
    if count != info.file_size:
        raise ValueError("candidate payload size mismatch after decompression")
    return digest.hexdigest()


def check_pe_header(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> None:
    """Validate AMD64/PE32+ *inside* the ZIP without extracting an executable."""
    with archive.open(info) as stream:
        dos = stream.read(64)
        if len(dos) != 64 or dos[:2] != b"MZ":
            raise ValueError("Baldosa candidate executable is not PE")
        header_offset = struct.unpack_from("<I", dos, 0x3C)[0]
        if header_offset < 64 or header_offset > min(16 * 1024 * 1024, info.file_size - 26):
            raise ValueError("Baldosa candidate executable PE offset invalid")
        stream.seek(header_offset)
        header = stream.read(26)
    if (len(header) != 26 or header[:4] != b"PE\0\0"
            or struct.unpack_from("<H", header, 4)[0] != 0x8664
            or struct.unpack_from("<H", header, 24)[0] != 0x20B):
        raise ValueError("Baldosa candidate executable must be AMD64 PE32+")


def check_launcher_policy(payload: bytes) -> bool:
    """Check invariant safety boundaries, not the evolving producer's byte template."""
    if (not payload.startswith(b"@echo off\r\n")
            or not payload.endswith(b"\r\n")
            or payload.replace(b"\r\n", b"").find(b"\n") != -1
            or b"\0" in payload):
        raise ValueError("Baldosa launcher has noncanonical CMD encoding or entry")
    # Older immutable packages have the original safe SETLOCAL entry;
    # current packages enable CMD extensions for UNC PUSHD mapping.
    entry = payload.split(b"\r\n", 2)[1]
    legacy_entry = b"setlocal DisableDelayedExpansion"
    mapped_entry = b"setlocal EnableExtensions DisableDelayedExpansion"
    if entry not in (legacy_entry, mapped_entry):
        raise ValueError("Baldosa launcher has noncanonical CMD encoding or entry")
    value = payload.decode("utf-8")
    critical = (
        'set "UR_BALDOSA_PACKAGE_DIR=%~dp0"',
        'set "UR_BALDOSA_ROM=%~dp0' + ROM + '"',
        "if not defined UR_RECOMP_USER_DATA_ROOT (",
        "[IO.Path]::IsPathRooted($d)",
        "[IO.Path]::GetFullPath($d)",
        "Get-FileHash -LiteralPath $env:UR_BALDOSA_ROM -Algorithm SHA256",
        USA_SHA256,
        "UR-BALDOSA-STARTUP-ROM-MISSING",
        "UR-BALDOSA-STARTUP-ROM-INVALID",
        'set "SNESRECOMP_USER_DATA_DIR=%UR_RECOMP_USER_DATA_ROOT%"',
        'set "UR_BALDOSA_MODERN_ROOT=1"',
        'set "UR_BALDOSA_MODERN_PROFILE_SELECT=1"',
        '--no-launcher "%UR_BALDOSA_ROM%" %*',
        'if "%ERRORLEVEL%"=="7"',
    )
    if (any(value.count(marker) != 1 for marker in critical)
            or "UR-BALDOSA-STARTUP-SAVE-ROOT" not in value):
        raise ValueError("Baldosa launcher missing canonical safety boundary")
    # Verify the exit contract, not a stale exact launcher template. Older
    # immutable packages exit directly with the native code. A mapped UNC
    # launcher must restore its temporary drive and preserve that code.
    legacy_exit = value.count("exit /b %ERRORLEVEL%") == 1
    mapped_exit = all(value.count(marker) == 1 for marker in (
        'pushd "%UR_RECOMP_USER_DATA_ROOT%"',
        ':UR-BALDOSA-CLEANUP\r\npopd\r\nexit /b %UR_BALDOSA_EXIT_CODE%',
        'set "UR_BALDOSA_EXIT_CODE=%ERRORLEVEL%"',
    ))
    if ((entry == legacy_entry and not legacy_exit)
            or (entry == mapped_entry and not mapped_exit)):
        raise ValueError("Baldosa launcher missing canonical safety boundary")
    if mapped_exit and (
            value.count("popd\r\n") != 1
            or value.index('pushd "%UR_RECOMP_USER_DATA_ROOT%"') >
               value.index('--no-launcher "%UR_BALDOSA_ROM%" %*')):
        raise ValueError("Baldosa launcher missing canonical safety boundary")
    # Existing older source revisions do not have a reparse walk. Report
    # their limitation without incorrectly asserting current-source identity.
    reparse = "[IO.FileAttributes]::ReparsePoint" in value
    if reparse and (value.index("ReparsePoint") > value.index("Get-FileHash")):
        raise ValueError("Baldosa launcher checks reparse ancestors too late")
    if (value.index("Get-FileHash") > value.index('set "SNESRECOMP_USER_DATA_DIR')
            or value.index('set "UR_BALDOSA_PACKAGE_DIR') >
               value.index("Get-FileHash")):
        raise ValueError("Baldosa launcher verification occurs after native setup")
    return reparse


def check_readme_policy(payload: bytes, source_sha: str) -> None:
    if (b"\r" in payload or not payload.endswith(b"\n")
            or b"\0" in payload):
        raise ValueError("Baldosa candidate README is not canonical LF text")
    value = payload.decode("utf-8")
    mandatory = (
        "NOT a completed remaster", "NOT a release or a beta approval",
        "The ROM and all profile/save data are ABSENT",
        "Required SHA-256: " + USA_SHA256,
        "Project source revision: " + source_sha,
    )
    if any(value.count(token) != 1 for token in mandatory):
        raise ValueError("Baldosa candidate README source or nonrelease policy mismatched")


def audit(archive_path: Path, source_sha: str, zip_sha256: str) -> dict:
    if not isinstance(source_sha, str) or not SHA40.fullmatch(source_sha):
        raise ValueError("Baldosa candidate needs nominated exact lowercase 40-hex commit")
    if not isinstance(zip_sha256, str) or not SHA256.fullmatch(zip_sha256):
        raise ValueError("Baldosa candidate needs nominated exact lowercase 64-hex ZIP digest")
    if archive_path.is_symlink() or not archive_path.is_file():
        raise ValueError("Baldosa candidate ZIP missing or symlink-backed")
    if archive_path.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("Baldosa candidate ZIP exceeds independent size budget")
    actual = file_digest(archive_path)
    if actual != zip_sha256:
        raise ValueError("Baldosa candidate ZIP differs from independently nominated digest")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            info = archive.infolist()
            names = [x.filename for x in info]
            if names != [PREFIX + x for x in EXPECTED]:
                raise ValueError("Baldosa candidate has extra, missing, duplicate or unordered members")
            for item in info:
                expected_limit = {
                    EXE: MAX_EXE_BYTES,
                    LAUNCHER: MAX_LAUNCHER_BYTES,
                    README: MAX_README_BYTES,
                    MANIFEST: MAX_MANIFEST_BYTES,
                }[item.filename.removeprefix(PREFIX)]
                if (item.is_dir() or item.file_size > expected_limit
                        or item.compress_type != zipfile.ZIP_DEFLATED
                        or item.date_time != ZIP_EPOCH
                        or item.external_attr != (0o100644 << 16)):
                    raise ValueError("Baldosa candidate contains noncanonical ZIP metadata")
            raw_manifest = archive.read(PREFIX + MANIFEST)
            try:
                metadata = json.loads(raw_manifest.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise ValueError("Baldosa candidate manifest malformed") from exc
            if (not isinstance(metadata, dict)
                    or raw_manifest != (json.dumps(metadata, sort_keys=True, indent=2) + "\n").encode("utf-8")):
                raise ValueError("Baldosa candidate manifest not canonical")
            expected_headers = {
                "format": "ur-recomp-baldosa-windows-x64-romless-candidate-v1",
                "project_revision": source_sha,
                "rom_bundled": False,
                "rom_filename": ROM,
                "rom_sha256_required": USA_SHA256,
                "profile_data_bundled": False,
                "status": "native-modern-root-stock-1p-2p-candidate-only",
            }
            if (set(metadata) != set(expected_headers) | {"immutable_files"}
                    or any(type(metadata.get(k)) is not type(v) or metadata[k] != v
                           for k, v in expected_headers.items())):
                raise ValueError("Baldosa candidate manifest identity, policy or source mismatched")
            listed = metadata.get("immutable_files")
            if (not isinstance(listed, list) or len(listed) != len(PAYLOAD_NAMES)
                    or [x.get("path") if isinstance(x, dict) else None for x in listed]
                       != list(PAYLOAD_NAMES)):
                raise ValueError("Baldosa candidate manifest payload inventory invalid")
            for entry in listed:
                if (set(entry) != {"path", "bytes", "sha256"}
                        or type(entry["bytes"]) is not int or entry["bytes"] <= 0
                        or not isinstance(entry["sha256"], str)
                        or not SHA256.fullmatch(entry["sha256"])):
                    raise ValueError("Baldosa candidate manifest payload metadata invalid")
                member = archive.getinfo(PREFIX + entry["path"])
                if member.file_size != entry["bytes"] or zip_member_digest(archive, member) != entry["sha256"]:
                    raise ValueError("Baldosa candidate payload digest or size mismatch")
            check_pe_header(archive, archive.getinfo(PREFIX + EXE))
            exe_digest = next(entry["sha256"] for entry in listed if entry["path"] == EXE)
            reparse_protected = check_launcher_policy(archive.read(PREFIX + LAUNCHER))
            check_readme_policy(archive.read(PREFIX + README), source_sha)
    except zipfile.BadZipFile as exc:
        raise ValueError("Baldosa candidate ZIP malformed or corrupt") from exc
    return make_envelope(
        evidence_type="provisional-baldosa-romless-zip-consistency",
        producer="tools/verify_baldosa_romless_candidate_qa.py",
        subject={"backend": "baldosa-aot-provisional",
                 "candidate_commit": source_sha,
                 "candidate_zip_sha256": actual},
        inputs={"artifact_basename": archive_path.name},
        assertions=[
            assertion("independently-nominated-source-and-zip-identity", True),
            assertion("romless-four-member-canonical-zip", True),
            assertion("manifest-and-all-payload-digests", True),
            assertion("amd64-pe32plus-inside-archive", True),
            assertion("launcher-and-readme-safety-invariants", True),
        ],
        metrics={"executable_payload_sha256": exe_digest,
                 "launcher_reparse_ancestor_guard_present": reparse_protected,
                 "launcher_rejects_rooted_but_relative_user_root_verified": False,
                 "launcher_absolute_save_override_windows_negative_executed": False,
                 "template_bytes_compared_against_matching_source_commit": False,
                 "physical_windows_verified": False,
                 "integrated_native_1p_2p_journey_verified": False,
                 "original_gameplay_parity_verified": False},
        outcome="inconclusive",
        provenance={"scope": "read-only ZIP consistency; not executed L4 or L5"},
    )


def audit_actions_wrapper(
    wrapper: Path, source_sha: str, inner_sha: str,
    *, expected_wrapper_sha: str | None = None,
) -> dict:
    """Check the unmodified two-member GitHub artifact as downloaded.

    The Actions artifact has its own, different SHA-256. The nomination must
    name the *inner* ZIP used by the actual Windows package, not this wrapper.
    A bounded temporary ROM-free ZIP is checked by the same strict consumer.
    """
    if (not isinstance(inner_sha, str) or not SHA256.fullmatch(inner_sha)
            or not isinstance(source_sha, str) or not SHA40.fullmatch(source_sha)):
        raise ValueError("Actions artifact needs externally nominated exact source and inner ZIP pins")
    if wrapper.is_symlink() or not wrapper.is_file():
        raise ValueError("Actions artifact wrapper missing or symlink-backed")
    if wrapper.stat().st_size > MAX_ZIP_BYTES + 2 * 1024 * 1024:
        raise ValueError("Actions artifact wrapper exceeds size limit")
    wrapper_digest = file_digest(wrapper)
    if expected_wrapper_sha is not None:
        if not isinstance(expected_wrapper_sha, str) or not SHA256.fullmatch(expected_wrapper_sha):
            raise ValueError("Actions wrapper nomination needs full lowercase SHA-256")
        if wrapper_digest != expected_wrapper_sha:
            raise ValueError("Actions wrapper bytes differ from independent SHA-256 nomination")
    try:
        with zipfile.ZipFile(wrapper) as archive:
            infos = archive.infolist()
            if [entry.filename for entry in infos] != [ACTIONS_INNER, ACTIONS_CHECKSUM]:
                raise ValueError("Actions artifact needs exactly one inner ZIP and checksum sidecar")
            if (infos[0].is_dir() or infos[1].is_dir()
                    or infos[0].file_size > MAX_ZIP_BYTES
                    or infos[1].file_size > 256):
                raise ValueError("Actions artifact contains oversized or directory members")
            sidecar = archive.read(ACTIONS_CHECKSUM)
            if sidecar != (inner_sha + " *" + ACTIONS_INNER + "\n").encode("ascii"):
                raise ValueError("Actions artifact sidecar does not match nominated inner ZIP SHA-256")
            with tempfile.TemporaryDirectory(prefix="ur-baldosa-qa-") as temporary:
                path = Path(temporary) / ACTIONS_INNER
                size = 0
                digest = hashlib.sha256()
                with archive.open(infos[0]) as reader, path.open("xb") as output:
                    while chunk := reader.read(BLOCK):
                        size += len(chunk)
                        if size > MAX_ZIP_BYTES:
                            raise ValueError("Actions inner ZIP exceeded size budget")
                        digest.update(chunk)
                        output.write(chunk)
                if digest.hexdigest() != inner_sha:
                    raise ValueError("Actions artifact inner ZIP bytes differ from nominated digest")
                report = audit(path, source_sha, inner_sha)
    except zipfile.BadZipFile as exc:
        raise ValueError("Actions artifact ZIP corrupt") from exc
    report["inputs"]["actions_wrapper_basename"] = wrapper.name
    report["inputs"]["actions_wrapper_sha256"] = wrapper_digest
    report["metrics"]["original_actions_sidecar_verified"] = True
    return report


RUNTIME_LAUNCHER = "Baldosa Native Extracted Launcher QA/launcher-acceptance.json"
RUNTIME_REPORT = "UR Baldosa Win32 Pause Route/report.json"
RUNTIME_ONE = "UR Baldosa Win32 Pause Route/modern_to_live_race_1p/log.txt"
RUNTIME_TWO = "UR Baldosa Win32 Pause Route/modern_to_live_race_2p/log.txt"
RUNTIME_NEW_ONE = "UR Baldosa Win32 Pause Route/native_real_1p_records/report.json"
RUNTIME_NEW_PLAYED = "UR Baldosa Win32 Pause Route/native_real_1p_records/played_native_event/log.txt"
RUNTIME_NEW_FRESH = "UR Baldosa Win32 Pause Route/native_real_1p_records/fresh_game_records/log.txt"
RUNTIME_NEW_TWO = "UR Baldosa Win32 Pause Route/native_real_2p_records/report.json"
RUNTIME_NEW_TWO_PLAYED = "UR Baldosa Win32 Pause Route/native_real_2p_records/played_native_2p/log.txt"
RUNTIME_NEW_TWO_FRESH = "UR Baldosa Win32 Pause Route/native_real_2p_records/fresh_game_2p_records/log.txt"

# Exact Windows Actions upload list, observed in successful hosted
# 1P/2P and first-racer Windows artifacts. An unreviewed extra ZIP member
# can carry private player data under an arbitrary .txt/.json suffix.
# The five stock diagnostic logs are allowed but never promoted as source
# result or fresh-Records evidence. Two product PRs proposed different exact
# first-racer upload layouts; only the first actually shipped green evidence.
# Only the proven first group is now source-checked against the genuine
# #1439 Win32 report and two real guest logs. The retired #1440 alternative
# remains a permitted but UNADMITTED complete diagnostic set. No human
# controller, saved-file byte or release-gate credit is inferred.
RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS = (
    (
        "UR Baldosa Win32 Pause Route/native_first_racer/report.json",
        "UR Baldosa Win32 Pause Route/native_first_racer/first_anonymous_process/log.txt",
        "UR Baldosa Win32 Pause Route/native_first_racer/fresh_named_process/log.txt",
    ),
    (
        "UR Baldosa Win32 Pause Route/native_first_racer_boot/report.json",
        "UR Baldosa Win32 Pause Route/native_first_racer_boot/first_controller_racer/log.txt",
        "UR Baldosa Win32 Pause Route/native_first_racer_boot/fresh_named_game/log.txt",
    ),
)
# New 3-game Windows product proof, distinct from the already accepted
# two-game first-racer boot and the fixture-created 1P/2P sources.
# A failed producer may upload three logs but no report; that MUST stay red.
# Optional raw launcher transcript. The original green no-arguments Windows
# producer archived its two success booleans but NOT this already-created log.
# Even when present, it is hosted script-driven evidence, not physical input.
RUNTIME_NOARGS_FIRST_RACER_LOG = (
    "Baldosa Native Extracted Launcher QA/first-racer-autorelaunch.log"
)
RUNTIME_FIRST_RACER_EARNED_GROUP = (
    "UR Baldosa Win32 Pause Route/native_first_racer_earned_records/report.json",
    "UR Baldosa Win32 Pause Route/native_first_racer_earned_records/new_user_creates_first_racer/log.txt",
    "UR Baldosa Win32 Pause Route/native_first_racer_earned_records/fresh_named_player_completes_race/log.txt",
    "UR Baldosa Win32 Pause Route/native_first_racer_earned_records/new_game_reopens_earned_records/log.txt",
)
# Product #1490's exact proposed *four-file* three-native-process bundle.
# A GO report is not an earned 2P result or independently observed source
# GO ticker, so never count these files as a finished match/release pass.
RUNTIME_SECOND_CREATED_RACER_GROUP = (
    "UR Baldosa Win32 Pause Route/native_real_second_racer/report.json",
    "UR Baldosa Win32 Pause Route/native_real_second_racer/first_P1_mike/log.txt",
    "UR Baldosa Win32 Pause Route/native_real_second_racer/named_P1_adds_P2/log.txt",
    "UR Baldosa Win32 Pause Route/native_real_second_racer/fresh_two_seat_source_go/log.txt",
)
RUNTIME_DIAGNOSTIC_LOGS = frozenset(
    "UR Baldosa Win32 Pause Route/" + suffix + "/log.txt"
    for suffix in (
        "baseline", "with_pause", "with_named_profile",
        "corrupt_named_profile", "different_named_profile",
    )
)
RUNTIME_ALLOWED_MEMBERS = frozenset((
    RUNTIME_LAUNCHER, RUNTIME_REPORT, RUNTIME_ONE, RUNTIME_TWO,
    RUNTIME_NEW_ONE, RUNTIME_NEW_PLAYED, RUNTIME_NEW_FRESH,
    RUNTIME_NEW_TWO, RUNTIME_NEW_TWO_PLAYED, RUNTIME_NEW_TWO_FRESH,
)) | RUNTIME_DIAGNOSTIC_LOGS | frozenset(
    name for group in RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS
    for name in group
) | frozenset(RUNTIME_FIRST_RACER_EARNED_GROUP) | frozenset(
    RUNTIME_SECOND_CREATED_RACER_GROUP
) | frozenset((
    RUNTIME_NOARGS_FIRST_RACER_LOG,
)) | PRODUCT_SOURCE_MEMBERS


def check_runtime_actions_wrapper(
    wrapper: Path, candidate: dict,
    *, expected_wrapper_sha: str | None = None,
) -> dict:
    """Read the separately produced same-run log/report archive without executing it.

    Positive claim: source-identical PE + bounded *entry to live race*.
    Two optional three-artifact groups add hosted source-bound native 1P
    and 2P result-to-Records evidence. A third exact, independently reviewed
    #1439 group adds anonymous-first-racer -> fresh-named-game source LOG
    consistency. Its SRAM/typed bytes, the 1P run and 2P pair remain absent.
    None can certify original parity, consumer hardware or release QA.
    """
    if wrapper.is_symlink() or not wrapper.is_file() or wrapper.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Baldosa Win32 runtime evidence ZIP missing, linked or oversized")
    if expected_wrapper_sha is not None:
        if not isinstance(expected_wrapper_sha, str) or not SHA256.fullmatch(expected_wrapper_sha):
            raise ValueError("runtime evidence nomination needs full lowercase SHA-256")
        if file_digest(wrapper) != expected_wrapper_sha:
            raise ValueError("runtime evidence wrapper differs from independent SHA-256 nomination")
    try:
        with zipfile.ZipFile(wrapper) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Baldosa runtime evidence has duplicate members")
            # The exact evidence producer's optional 1P/2P groups are
            # independently checked all-or-none below. A nonallowlisted
            # attachment is never silently accepted merely because it is
            # called .txt, .json, .log or lacks a known ROM/save extension.
            # This also rejects directories, path aliases, traversal and
            # unreviewed private data before any member is read.
            if not set(names) <= RUNTIME_ALLOWED_MEMBERS:
                raise ValueError("Baldosa runtime evidence has unreviewed ZIP member")
            # All members, including the five diagnostic logs that this QA
            # consumer intentionally never reads, must be bounded. Otherwise
            # an allowlisted filename can conceal a huge compressed private
            # export/ZIP bomb which survives the outer 16 MiB size cap.
            if any(
                item.is_dir() or not 0 < item.file_size <= 2 * 1024 * 1024
                for item in archive.infolist()
            ):
                raise ValueError("Baldosa runtime evidence has oversized/empty ZIP member")
            first_racer_sets = [
                sum(path in names for path in group)
                for group in RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS
            ]
            if any(count not in (0, 3) for count in first_racer_sets):
                raise ValueError("Baldosa first-racer diagnostic evidence group incomplete")
            if sum(count == 3 for count in first_racer_sets) > 1:
                raise ValueError("Baldosa first-racer diagnostic evidence groups ambiguous")
            earned_count = sum(
                member in names for member in RUNTIME_FIRST_RACER_EARNED_GROUP
            )
            if earned_count not in (0, 4):
                raise ValueError("Baldosa first-racer earned 1P evidence group incomplete")
            second_racer_count = sum(
                name in names for name in RUNTIME_SECOND_CREATED_RACER_GROUP
            )
            if second_racer_count not in (0, 4):
                raise ValueError("Baldosa second-racer source evidence group incomplete")

            def bounded(name: str, limit: int) -> bytes:
                try:
                    entry = archive.getinfo(name)
                except KeyError as exc:
                    raise ValueError("Baldosa runtime evidence missing required report/log") from exc
                if entry.is_dir() or not 0 < entry.file_size <= limit:
                    raise ValueError("Baldosa runtime evidence entry empty or oversized")
                return archive.read(entry)

            raw_report = bounded(RUNTIME_REPORT, 256 * 1024)
            raw_launcher = bounded(RUNTIME_LAUNCHER, 64 * 1024)
            log1 = bounded(RUNTIME_ONE, 2 * 1024 * 1024)
            log2 = bounded(RUNTIME_TWO, 2 * 1024 * 1024)
            newer_one_names = (RUNTIME_NEW_ONE, RUNTIME_NEW_PLAYED, RUNTIME_NEW_FRESH)
            newer_one_present = [name in names for name in newer_one_names]
            if any(newer_one_present) and not all(newer_one_present):
                raise ValueError("Baldosa native 1P result-to-Records evidence group incomplete")
            newer_one = (
                (bounded(RUNTIME_NEW_ONE, 64 * 1024),
                 bounded(RUNTIME_NEW_PLAYED, 2 * 1024 * 1024),
                 bounded(RUNTIME_NEW_FRESH, 2 * 1024 * 1024))
                if all(newer_one_present) else None
            )
            newer_two_names = (
                RUNTIME_NEW_TWO, RUNTIME_NEW_TWO_PLAYED, RUNTIME_NEW_TWO_FRESH,
            )
            newer_two_present = [name in names for name in newer_two_names]
            if any(newer_two_present) and not all(newer_two_present):
                raise ValueError("Baldosa native 2P paired result-to-Records evidence group incomplete")
            newer_two = (
                (bounded(RUNTIME_NEW_TWO, 64 * 1024),
                 bounded(RUNTIME_NEW_TWO_PLAYED, 2 * 1024 * 1024),
                 bounded(RUNTIME_NEW_TWO_FRESH, 2 * 1024 * 1024))
                if all(newer_two_present) else None
            )
            # The first, now-real first-racer producer layout is a complete
            # source-owned triad. The retired second layout is intentionally
            # still a bounded noncredited diagnostic, never a substitute.
            new_first_racer = (
                (bounded(RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS[0][0], 64 * 1024),
                 bounded(RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS[0][1], 2 * 1024 * 1024),
                 bounded(RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS[0][2], 2 * 1024 * 1024))
                if first_racer_sets[0] == 3 else None
            )
            new_first_racer_earned = (
                tuple(bounded(member, 64 * 1024 if i == 0 else 2 * 1024 * 1024)
                      for i, member in enumerate(RUNTIME_FIRST_RACER_EARNED_GROUP))
                if earned_count == 4 else None
            )
            new_second_racer_go = (
                tuple(
                    bounded(name, 64 * 1024 if i == 0 else 2 * 1024 * 1024)
                    for i, name in enumerate(RUNTIME_SECOND_CREATED_RACER_GROUP)
                )
                if second_racer_count == 4 else None
            )
            noargs_launcher_log = (
                bounded(RUNTIME_NOARGS_FIRST_RACER_LOG, 2 * 1024 * 1024)
                if RUNTIME_NOARGS_FIRST_RACER_LOG in names else None
            )
            product_source_metrics = audit_extra_hosted_groups(archive)
    except zipfile.BadZipFile as exc:
        raise ValueError("Baldosa Win32 runtime evidence ZIP is corrupt") from exc
    try:
        reported = json.loads(raw_report.decode("utf-8"))
        launcher = json.loads(raw_launcher.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Baldosa runtime reports contain invalid JSON") from exc
    if not isinstance(reported, dict) or not isinstance(launcher, dict):
        raise ValueError("Baldosa runtime reports must be JSON objects")
    if (reported.get("exe_sha256") != candidate["metrics"]["executable_payload_sha256"]
            or launcher.get("archive_sha256") != candidate["subject"]["candidate_zip_sha256"]):
        raise ValueError("Win32 tested executable/launcher ZIP does not match candidate bytes")
    if not all(launcher.get(field) is True for field in (
        "real_extracted_launcher_accepted",
        "published_zip_unchanged", "rom_not_in_archive",
        "canonical_8192_byte_save_outside_package",
    )):
        raise ValueError("Win32 extracted CMD launcher was not confirmed")
    # Future real native CMD no-args evidence must preserve BOTH explicit
    # product assertions if either is mentioned. An unarchived log is not
    # an independently observed source sequence, even when both are true.
    cmd_report_fields = (
        "no_argument_first_racer_cmd_one_shot_restart_accepted",
        "fresh_named_game_after_actual_cmd_restart",
    )
    cmd_reported = any(field in launcher for field in cmd_report_fields)
    if cmd_reported and any(launcher.get(field) is not True
                            for field in cmd_report_fields):
        raise ValueError("incomplete/contradictory no-args CMD producer report")
    if noargs_launcher_log is not None:
        if not cmd_reported:
            raise ValueError("CMD raw launcher trace is unbound to a positive producer report")
        cmd_metrics = audit_win32_cmd_first_racer_source(noargs_launcher_log)
        candidate["metrics"].update(cmd_metrics)
        candidate["assertions"].append(
            assertion("hosted-cmd-noargs-first-racer-two-native-roots-source-log-consistent", True)
        )
    else:
        candidate["metrics"]["hosted_cmd_two_native_roots_one_first_racer_restart_log_consistent"] = False
        candidate["metrics"]["hosted_cmd_log_independently_recomputed"] = False
        candidate["metrics"]["hosted_physical_gamepad_verified"] = False
    candidate["metrics"]["hosted_cmd_noargs_first_racer_restart_producer_reported"] = (
        cmd_reported
    )
    candidate["metrics"]["hosted_cmd_noargs_first_racer_restart_producer_reported_only"] = (
        cmd_reported and noargs_launcher_log is None
    )
    if (reported.get("classification") != "windows_native_pause_and_named_profile_smoke_only"
            or type(reported.get("course_complete_credit")) is not int
            or reported["course_complete_credit"] != 0
            or reported.get("physical_gamepad_hardware_tested") is not False
            or not isinstance(reported.get("native_named_readonly_records"), dict)
            or reported["native_named_readonly_records"].get("actual_native_2p_match_published") is not False):
        raise ValueError("Baldosa runtime artifact cannot be admitted as incomplete hosted smoke")
    history = reported["native_named_readonly_records"]
    historical_fields = (
        "canonical_2p_archive_readonly_tabs_checked",
        "historical_2p_pairs_read",
        "incomplete_2p_pairs_reported_unavailable",
        "2p_archive_unchanged_after_guest",
        "unbound_2p_never_attributed_to_a_record",
        "no_run_created_by_record_view_or_script_quit",
    )
    has_history = any(key in history for key in historical_fields)
    if has_history:
        # Do not cherry-pick a reassuring count from an incomplete report:
        # every safety qualifier must be present and consistent.
        if (any(key not in history for key in historical_fields)
                or any(history[key] is not True for key in (
                    "canonical_2p_archive_readonly_tabs_checked",
                    "2p_archive_unchanged_after_guest",
                    "unbound_2p_never_attributed_to_a_record",
                    "no_run_created_by_record_view_or_script_quit",
                ))
                or any(type(history[key]) is not int
                       or not 0 <= history[key] <= 10000
                       for key in ("historical_2p_pairs_read",
                                   "incomplete_2p_pairs_reported_unavailable"))):
            raise ValueError("hosted 2P read-only Records report has missing or contradictory safety claims")
    for players, log, field in (
        (1, log1, "modern_root_race_entry_p1"),
        (2, log2, "modern_root_race_entry_p2"),
    ):
        entry = reported.get(field)
        if (not isinstance(entry, dict)
                or type(entry.get("players")) is not int
                or entry["players"] != players
                or entry.get("native_root_handoff_observed") is not True
                or entry.get("original_race_nmi_barrier_passed") is not True
                or entry.get("original_go_ticker_barrier_passed") is not True
                or entry.get("complete_event_outcome_claimed") is not False
                or type(entry.get("actual_guest_frames")) is not int
                or entry["actual_guest_frames"] <= 0):
            raise ValueError("Baldosa hosted stock-race entry report inconsistent")
        contents = log.decode("utf-8", "replace")
        markers = (
            f"UR_BALDOSA_MODERN_ROOT stock_entered players={players}",
            "SDL reports 0 joystick(s)",
            "audio=dummy",
        )
        # The real guest transcript includes both "script f=... quit" and
        # "exit: script quit"; counting the substring " quit" double-counts.
        script_exits = re.findall(r"(?m)^script f=[0-9]+ quit\r?$", contents)
        if (any(contents.count(marker) != 1 for marker in markers)
                or len(script_exits) != 1
                or "UR_MULTIPLAYER_MATCH " in contents
                or "UR_RUN_RECORD " in contents):
            raise ValueError("Baldosa stock-race entry log missing or contradicts smoke scope")
    # Read the producer's *three* coarchived source-result/fresh-game files
    # as one optional set; never mint 1P Records credit from only a happy JSON
    # boolean or a newly saved record's unaudited SHA string.
    if newer_one is not None:
        record_metrics = audit_hosted_native_1p_records(*newer_one)
        candidate["metrics"].update(record_metrics)
        candidate["assertions"].append(
            assertion("hosted-native-1p-result-and-fresh-game-records-logs-consistent", True)
        )
    else:
        candidate["metrics"]["hosted_native_1p_result_to_fresh_records_logs_consistent"] = False
        candidate["metrics"]["hosted_saved_urrun_bytes_independently_reopened"] = False
    # Fail closed on any incomplete guest 2P result / pair / fresh-game
    # archive; a source finish with published=0 is NOT a paired Records pass.
    if newer_two is not None:
        paired_metrics = audit_hosted_native_2p_records(*newer_two)
        candidate["metrics"].update(paired_metrics)
        candidate["assertions"].append(
            assertion("hosted-source-2p-atomic-pair-and-fresh-game-records-logs-consistent", True)
        )
    else:
        candidate["metrics"]["hosted_native_2p_result_to_fresh_records_logs_consistent"] = False
        candidate["metrics"]["hosted_saved_2p_pair_bytes_independently_reopened"] = False
    if new_first_racer is not None:
        first_racer_metrics = audit_hosted_win32_first_racer(*new_first_racer)
        candidate["metrics"].update(first_racer_metrics)
        candidate["assertions"].append(
            assertion("hosted-first-racer-creation-to-fresh-named-guest-logs-consistent", True)
        )
    else:
        candidate["metrics"]["hosted_first_racer_anonymous_creation_to_fresh_named_boot_consistent"] = False
        candidate["metrics"]["hosted_created_profile_bytes_independently_rehashed"] = False
        candidate["metrics"]["hosted_one_shot_packaged_launcher_restart_verified"] = False
    if new_first_racer_earned is not None:
        earned_metrics = audit_hosted_first_racer_earned_1p(*new_first_racer_earned)
        candidate["metrics"].update(earned_metrics)
        candidate["assertions"].append(
            assertion("hosted-first-racer-actual-earned-1p-three-native-game-records-logs-consistent", True)
        )
    else:
        candidate["metrics"]["hosted_first_racer_earned_1p_three_game_logs_consistent"] = False
        candidate["metrics"]["hosted_saved_urrun_bytes_independently_decoded"] = False
    if new_second_racer_go is not None:
        p2_creation = audit_win32_second_created_racer_go(*new_second_racer_go)
        candidate["metrics"].update(p2_creation)
        candidate["assertions"].append(
            assertion("hosted-second-player-created-and-two-seat-stock-entry-source-logs-consistent", True)
        )
    else:
        candidate["metrics"]["hosted_new_mike_and_andrew_to_two_seat_stock_entry_logs_consistent"] = False
        candidate["metrics"]["hosted_p2_catalog_and_sram_bytes_independently_rehashed"] = False
        candidate["metrics"]["hosted_original_guest_stock_two_player_go_barrier_independently_observed"] = False
    candidate["inputs"]["runtime_actions_wrapper_basename"] = wrapper.name
    candidate["inputs"]["runtime_actions_wrapper_sha256"] = file_digest(wrapper)
    for name, raw in (
        ("win32_runtime_report_sha256", raw_report),
        ("win32_extracted_launcher_report_sha256", raw_launcher),
        ("win32_1p_entry_log_sha256", log1),
        ("win32_2p_entry_log_sha256", log2),
    ):
        candidate["inputs"][name] = hashlib.sha256(raw).hexdigest()
    candidate["assertions"].append(
        assertion("same-run-win32-executable-identity-and-stock-race-entry-logs", True)
    )
    candidate["metrics"]["hosted_1p_stock_entry_observed"] = True
    candidate["metrics"]["hosted_2p_stock_entry_observed"] = True
    candidate["metrics"].update(product_source_metrics)
    if product_source_metrics[
        "hosted_real_six_native_process_ui_created_pair_and_both_records_log_consistent"
    ]:
        candidate["assertions"].append(assertion(
            "hosted-six-native-process-created-pair-scored-ui-selected-records-source-logs-consistent",
            True,
        ))
    elif product_source_metrics[
        "hosted_real_five_native_process_backend_selected_pair_log_consistent"
    ]:
        candidate["assertions"].append(assertion(
            "hosted-five-native-process-created-pair-scored-backend-selected-records-source-logs-consistent",
            True,
        ))
    if product_source_metrics[
        "hosted_real_existing_p1_switch_both_directions_log_consistent"
    ]:
        candidate["assertions"].append(assertion(
            "hosted-native-existing-profile-selector-both-directions-source-logs-consistent",
            True,
        ))
    if product_source_metrics[
        "hosted_first_anonymous_nondefault_andrew_source_boot_log_consistent"
    ]:
        candidate["assertions"].append(assertion(
            "hosted-first-nondefault-andrew-source-created-and-fresh-boot-logs-consistent",
            True,
        ))
    # An empty-but-read-only tab is a valid negative safety observation,
    # not positive evidence that a historical saved match was visible.
    visible_history = has_history and history["historical_2p_pairs_read"] > 0
    candidate["metrics"]["historical_2p_records_readonly_observed"] = visible_history
    candidate["metrics"]["historical_2p_records_tabs_checked"] = has_history
    if has_history:
        candidate["metrics"]["historical_2p_pairs_read"] = history["historical_2p_pairs_read"]
        candidate["metrics"]["incomplete_2p_pairs_unavailable"] = (
            history["incomplete_2p_pairs_reported_unavailable"]
        )
    if visible_history:
        candidate["assertions"].append(
            assertion("hosted-historical-2p-records-visible-without-mutation-or-publication", True)
        )
    # A guest-settled native 1P result is now observable from the three
    # source/result/Records logs; it still has no independent original oracle
    # or physical-device standing. No paired native 2P match is reported.
    candidate["metrics"]["finished_native_event_or_new_match_observed"] = (
        newer_one is not None or newer_two is not None
        or new_first_racer_earned is not None
    )
    candidate["metrics"]["strict_original_native_complete_event_accepted"] = False
    candidate["metrics"]["new_native_two_player_match_published"] = newer_two is not None
    candidate["metrics"]["physical_gamepad_hardware_verified"] = False
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--zip", type=Path, help="inner ROM-free candidate ZIP")
    input_group.add_argument("--actions-artifact", type=Path, help="two-member Actions ZIP as downloaded")
    parser.add_argument("--runtime-evidence", type=Path,
                        help="same-run small ROM-free Win32 report/log Actions artifact; requires --actions-artifact")
    parser.add_argument("--expected-actions-artifact-sha256",
                        help="externally nominated GitHub candidate wrapper SHA-256")
    parser.add_argument("--expected-runtime-evidence-sha256",
                        help="externally nominated Windows runtime evidence wrapper SHA-256")
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--expected-zip-sha256", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.runtime_evidence is not None and args.actions_artifact is None:
        parser.error("--runtime-evidence requires the exact --actions-artifact ZIP")
    if (args.actions_artifact is None) != (args.expected_actions_artifact_sha256 is None):
        parser.error("--actions-artifact requires the externally nominated wrapper SHA-256")
    if (args.runtime_evidence is None) != (args.expected_runtime_evidence_sha256 is None):
        parser.error("--runtime-evidence requires the externally nominated wrapper SHA-256")
    try:
        if args.actions_artifact is not None:
            result = audit_actions_wrapper(
                args.actions_artifact, args.expected_source, args.expected_zip_sha256,
                expected_wrapper_sha=args.expected_actions_artifact_sha256,
            )
        else:
            result = audit(args.zip, args.expected_source, args.expected_zip_sha256)
        if args.runtime_evidence is not None:
            result = check_runtime_actions_wrapper(
                args.runtime_evidence, result,
                expected_wrapper_sha=args.expected_runtime_evidence_sha256,
            )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        # A reviewed receipt is immutable. Never silently replace an existing
        # output, including a symlink to another report or player file.
        try:
            with args.output.open("x", encoding="utf-8") as destination:
                destination.write(rendered)
        except OSError as exc:
            parser.error(f"cannot create a new independent QA receipt: {exc}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
