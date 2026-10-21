#!/usr/bin/env python3
"""Fail-closed whole-run audit for the *original* Modern Win32 Actions ZIPs.

Requires all six distinct capture archives from one exact source checkout,
one separately retained actual AMD64 Windows PE, and every one of the 21
documented Modern/Authentic routes. Reuses the source/SDL P7/PNG pixel and
log validation in qa_modern_visual_actions_archive rather than treating
a producer-written receipt or a CI green check as independent evidence.

This verifies transport, executable identity and observed native state.
It deliberately NEVER grants aesthetic, hardware, guest-CRC or release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

# Support both `python -m tools.qa_modern_visual_actions_batch` and direct
# `python tools/qa_modern_visual_actions_batch.py` from a clean checkout.
if __package__:
    from tools import qa_modern_visual_actions_archive as capture
else:
    import qa_modern_visual_actions_archive as capture

EXPECTED = {
    "root": {
        "ur-modern-win32-visual-1024x768": "root-quit",
        "ur-modern-win32-visual-1280x720": "root-quit",
    },
    "authentic": {
        "ur-authentic-win32-control-1024x768": "authentic-stock",
        "ur-authentic-win32-control-1280x720": "authentic-stock",
    },
    "play": {
        "ur-modern-win32-play-stock-1024x768": "play-stock-handoff",
        "ur-modern-win32-play-stock-1280x720": "play-stock-handoff",
    },
    "navigation": {
        "ur-modern-win32-journey-records-keyboard": "records-keyboard",
        "ur-modern-win32-journey-options-p1": "options-p1",
        "ur-modern-win32-journey-profile-first-p1": "profile-first-p1",
        "ur-modern-win32-journey-practice-picker-p1": "practice-picker-p1",
        "ur-modern-win32-journey-multiplayer-unbound": "multiplayer-unbound",
    },
    "wide_destinations": {
        "ur-modern-win32-wide-destination-records-keyboard": "records-keyboard",
        "ur-modern-win32-wide-destination-options-open-p1": "options-open-p1",
        "ur-modern-win32-wide-destination-profile-first-p1": "profile-first-p1",
        "ur-modern-win32-wide-destination-practice-picker-p1": "practice-picker-p1",
        "ur-modern-win32-wide-destination-multiplayer-unbound": "multiplayer-unbound",
    },
    "title": {
        "ur-integrated-title-title-intro-compact": "title-intro-compact",
        "ur-integrated-title-title-intro-wide": "title-intro-wide",
        "ur-integrated-title-title-intro-reduced": "title-intro-reduced",
        "ur-integrated-title-title-transition-root": "title-transition-root",
        "ur-integrated-title-title-transition-root-reduced": "title-transition-root-reduced",
    },
}
EXE_NAME = "UniracersSNESRecomp.exe"
MAX_PE = 80 * 1024 * 1024


class BundleError(ValueError):
    pass


def native_exe_sha(path: Path) -> tuple[str, int]:
    if not path.is_file() or path.is_symlink():
        raise BundleError("native PE archive absent or redirected")
    with zipfile.ZipFile(path) as z:
        files = [x for x in z.infolist() if not x.is_dir()]
        if len(files) != 1 or files[0].filename != EXE_NAME:
            raise BundleError("must have exactly one unchanged native executable")
        if not 65536 <= files[0].file_size <= MAX_PE:
            raise BundleError("native executable bytes missing or implausible")
        pe = z.read(files[0])
    if pe[:2] != b"MZ":
        raise BundleError("native executable missing DOS MZ signature")
    pos = struct.unpack_from("<I", pe, 0x3c)[0]
    if (pos < 64 or pos + 26 >= len(pe) or
            pe[pos:pos+4] != b"PE\0\0" or
            struct.unpack_from("<H", pe, pos+4)[0] != 0x8664 or
            struct.unpack_from("<H", pe, pos+24)[0] != 0x20b):
        raise BundleError("native executable is not Windows AMD64 PE32+")
    return hashlib.sha256(pe).hexdigest(), len(pe)


def verify(
    archives: dict[str, Path], native_executable: Path,
    source_sha: str, expected_exe_sha: str | None = None,
) -> dict:
    if set(archives) != set(EXPECTED):
        raise BundleError("six original Win32 capture archive roles required")
    if not capture.SOURCE_HEX.fullmatch(source_sha):
        raise BundleError("exact 40-character source checkout SHA required")
    if len({str(p.resolve()) for p in [*archives.values(), native_executable]}) != 7:
        raise BundleError("capture and executable archive paths cannot be reused")
    executable_sha, executable_bytes = native_exe_sha(native_executable)
    if expected_exe_sha is not None and (
            not capture.HEX.fullmatch(expected_exe_sha) or
            executable_sha != expected_exe_sha):
        raise BundleError("downloaded AMD64 PE does not match required SHA256")
    all_cases: list[dict] = []
    for role, required in EXPECTED.items():
        archive = archives[role]
        if not archive.is_file() or archive.is_symlink():
            raise BundleError("required capture artifact absent or redirected: " + role)
        result = capture.verify(
            archive, expected_source_sha=source_sha,
            expected_exe_sha=executable_sha)
        observed = {case["id"]: case for case in result["captures"]}
        if (len(observed) != len(result["captures"]) or
                set(observed) != set(required)):
            missing = sorted(set(required) - set(observed))
            extra = sorted(set(observed) - set(required))
            raise BundleError(
                f"{role}: missing/duplicate/extra native screenshots; "
                f"missing={missing} extra={extra}")
        for case_id, expected_route in required.items():
            case = observed[case_id]
            # A coherent route has already been checked independently by
            # the source-stage and SDL readback consumer. The route identity
            # is made explicit in that consumer's returned observation.
            if case.get("native_semantic_route") != expected_route:
                raise BundleError(
                    f"{role}: wrong route for {case_id}: "
                    f"{case.get('native_semantic_route')}")
            all_cases.append(case)
    if len(all_cases) != 21:
        raise BundleError("21 distinct exact native cases are mandatory")
    return {
        "schema_version": 1,
        "native_executable":EXE_NAME,
        "native_executable_sha256":executable_sha,
        "native_executable_bytes":executable_bytes,
        "source_sha":source_sha,
        "real_original_artifact_roles":sorted(EXPECTED),
        "verified_exact_sdl_png_p7_native_route_cases":len(all_cases),
        "title_source_FNV_witnesses":sum(
            x.get("verified_native_title_source") is not None for x in all_cases),
        "cases":all_cases,
        "complete_transport_and_source_provenance":True,
        "human_visual_approved":False,
        "hardware_approved":False,
        "authentic_gameplay_crc_approved":False,
        "release_gate_credit":0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for role in EXPECTED:
        p.add_argument("--"+role.replace("_", "-"),required=True,type=Path)
    p.add_argument("--native-executable",required=True,type=Path)
    p.add_argument("--source-sha",required=True)
    p.add_argument("--expected-exe-sha")
    p.add_argument("--report",type=Path)
    opts=p.parse_args()
    archives={
        role:getattr(opts,role) for role in EXPECTED
    }
    try:
        result=verify(archives,opts.native_executable,
                      opts.source_sha,opts.expected_exe_sha)
        if opts.report:
            if opts.report.exists() or opts.report.is_symlink():
                raise BundleError("report destination must not preexist")
            opts.report.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
        return 0
    except (BundleError,capture.AuditError,ValueError,KeyError,IndexError,OSError,
            zipfile.BadZipFile) as exc:
        print("MODERN_COMBINED_WINDOWS_NATIVE_EVIDENCE_REJECTED:",str(exc))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
