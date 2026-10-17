#!/usr/bin/env python3
"""Independent Windows original-source PPU check on one real 2P AOT route.

Executes the EXISTING Windows route runner on the SAME binary as Modern
journeys. Its optional post-original-PPU hook writes actual (not synthesized)
256x224 PAM frames. Verify raw whole-file SHA against already independently
accepted original/native 2P raster identities, with no temporal interpolation,
resizing, shift, ignored rows, invented pixel ownership or acceptance waiver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

try:
    from tools.baldosa_windows_native_pause_route import run_route
except ImportError:
    from baldosa_windows_native_pause_route import run_route

EXPECTED = {
    # Four source-qualified P7 identities: original callback 1855 -> guest 1856,
    # and three distinct genuine moving split-screen original callbacks.
    1856: "ed35731cde55e927165f173c1db29c27b3b7eeff19862fbca27db3467cb8bc87",
    2192: "fac9f37e04b752676346bd75345e6e988b88e5cf6703722618d8a968ec90b36c",
    2208: "bf8b4218fb72f94338b19da5c1386bd5ce09c0dc0c767093286e80895fa3353c",
    2224: "d64e7b2fee2ff9f21b5fad7f4e8618ea27ad8846c6b6047ca9c511583bde6bd8",
}
FRAMES = (1856, 2192, 2208, 2224)
# Exact 2473-field input population, independent of the *other* 5484-field
# race_2p.txt source route. The short route inserts different post-GO holds
# (and thus idle host ticks); cross-route moving pixels are not parity evidence.
SHORT_2P_SCRIPT_CRLF_SHA256 = "4e714899f53c3bbe501bbfcacf91dd549989c9beb7c2cf6265b13eb687142ec6"
SHORT_2P_GUEST_CRC_SHA256 = "992dfdc270802e8a0ec1be5a0be6ddc36872edca11c8a91d58367a6235e537cf"
# 2P stock source digests for the same game/input/window (no use as tolerances).
STOCK = {
    1856: "6aea6cebaf1292d962ad5ce01a73966bb0ad8948095d1e73b155712cac41039a",
    2192: "7e0cfab20c5342c242d7eeb0c77bff2d132ee1426a62d3a3759f43bd3f95027e",
    2208: "a946c9ebb54775639b8fd87a6861af0408cceed4896e58be05908c4a4491c67f",
    2224: "8271ed54cc2f1c1841cbd0f1e0c6b77e278dce721a2e1efe1a6ba432897535b4",
}
LOG = re.compile(
    r"^UR_QA08_WINDOWS_ORIGINAL_SOURCE frame=(\d+) logical=256x224 "
    r"saved=1 source=post-original-ppu-before-present$", re.M,
)
HEADER = (
    b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
    b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
)
SIZE = len(HEADER) + 256 * 224 * 4


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_full_route_identity(route_sha: str, guest_crc_sha: str) -> None:
    """Fail closed if four pictures match but guest/script provenance drifted."""
    if route_sha != SHORT_2P_SCRIPT_CRLF_SHA256:
        raise ValueError("not the exact source-pinned short 2P script/CRLF checkout")
    if guest_crc_sha != SHORT_2P_GUEST_CRC_SHA256:
        raise ValueError("real 2473-frame short 2P guest CRC transcript has drifted")


def check_current_core_control(route_sha: str, actual: list[str], control: list[str]) -> dict:
    """Validate a second genuine process on *identical* integrated RF-017 code.

    The legacy before-RF017 2473-frame SHA is retained as a historical negative,
    not silently re-labelled as a new core source identity. Without an
    independent same-PE/same-input process this graphics source witness fails.
    """
    if route_sha != SHORT_2P_SCRIPT_CRLF_SHA256:
        raise ValueError("independent control was not the exact short 2P route")
    if len(actual) != 2473 or len(control) != 2473:
        raise ValueError("independent same-core Windows control missing guest frames")
    if any(not re.fullmatch(r"0x[0-9a-fA-F]{8}", c)
           for c in actual + control):
        raise ValueError("malformed real guest CRC in independent Windows control")
    divergence = next((i + 1 for i, (a, b) in enumerate(zip(actual, control))
                       if a.lower() != b.lower()), None)
    if divergence is not None:
        raise ValueError(f"independent same-core native guest WRAM diverged frame={divergence}")
    digest = sha256(("\n".join(x.lower() for x in control) + "\n").encode("ascii"))
    return {
        "independent_same_core_guest_frames": 2473,
        "independent_same_core_guest_CRC_sha256": digest,
        "independent_guest_transcript_exact": True,
        "legacy_pre_RF017_transcript_matches": digest == SHORT_2P_GUEST_CRC_SHA256,
        "no_pre_RF017_guest_equivalence_claimed": True,
    }


def inspect(source: Path, log: str, crcs: list[str]) -> dict:
    if len(crcs) != 2473 or any(not re.fullmatch(r"0x[0-9a-fA-F]{8}", s) for s in crcs):
        raise ValueError("incomplete or malformed original USA native 2P guest CRCs")
    emitted = [int(x) for x in LOG.findall(log)]
    if len(emitted) != len(set(emitted)) or any(f not in FRAMES for f in emitted):
        raise ValueError("duplicate or unsolicited PPU callback source witness")
    if re.search(r"^UR_QA08_WINDOWS_SOURCE_REJECT", log, re.M):
        raise ValueError("PPU source writer signalled a bad or repeated capture")
    observed = sorted(source.glob("ur-baldosa-original-source-*.pam"))
    got = {}
    for path in observed:
        match = re.fullmatch(r"ur-baldosa-original-source-(\d{6})\.pam", path.name)
        if not match or int(match[1]) not in FRAMES:
            raise ValueError("unrecognized additional source raster")
        frame = int(match[1])
        blob = path.read_bytes()
        if len(blob) != SIZE or not blob.startswith(HEADER):
            raise ValueError(f"frame {frame} was cropped or corrupt, not a 256x224 native P7")
        if frame in got:
            raise ValueError("two source rasters use the same actual frame ID")
        got[frame] = sha256(blob)
    if set(got) != set(emitted):
        raise ValueError("saved PPU source files do not match exact callback log")
    # 2208 was the already accepted Linux guest callback. Missing on a
    # different SDL host is MISSING evidence, not nearest-frame success.
    # Record other host-presented frames and check them if actually emitted.
    controls = [{
        "actual_guest_frame": frame,
        "actual_source_P7_sha256": got[frame],
        "expected_independent_disposable_global_prime_P7_sha256": EXPECTED.get(frame),
        "matches_original_native_2p_source_raster": (
            got[frame] == EXPECTED[frame] if frame in EXPECTED else None
        ),
        "matches_old_wrong_pinned_native_raster": (
            got[frame] == STOCK[frame] if frame in STOCK else None
        ),
    } for frame in sorted(got)]
    return {
        "schema": "qa08-windows-source-bound-2P-original-ppu-candidate/1",
        "actual_complete_native_guest_frames": len(crcs),
        "actual_native_guest_CRC_sha256": sha256(
            ("\n".join(s.lower() for s in crcs) + "\n").encode("ascii")),
        "source_geometry": [256, 224],
        "actual_frames_observed": sorted(got),
        "source_sha_controls": controls,
        "source_callback_2208_observed": 2208 in got,
        "source_callback_2208_match_to_independent_original": (
            got.get(2208) == EXPECTED[2208]),
        "observed_moving_postGO_frames_all_exact": (
            all(got.get(frame) == EXPECTED[frame]
                for frame in (2192, 2208, 2224))),
        "all_four_countdown_and_moving_2P_original_source_exact": (
            set(got) == set(FRAMES)
            and all(got[frame] == EXPECTED[frame] for frame in FRAMES)),
        "unchanged_1P_original_source_and_2P_results_not_admitted": True,
        "no_changed_guest_logic_or_modern_business": True,
        "release_graphics_gate_approved": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", required=True, type=Path)
    ap.add_argument("--rom", required=True, type=Path)
    ap.add_argument("--script", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--video", default="windows")
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()
    if args.out.exists():
        ap.error("refusing existing capture root")
    route_sha = sha256(args.script.read_bytes())
    if route_sha != SHORT_2P_SCRIPT_CRLF_SHA256:
        ap.error("original short 2P script SHA has drifted: not source-qualified")
    args.out.mkdir(parents=True)
    source = args.out / "source"
    source.mkdir()
    # Only one real independent Windows process is authorized to write here.
    previous = os.environ.get("UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR")
    os.environ["UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR"] = str(source.resolve())
    try:
        crcs, log = run_route(args.exe.resolve(), args.rom.resolve(),
                              args.script.resolve(), args.out,
                              pause=False, video=args.video,
                              timeout=args.timeout)
    finally:
        if previous is None:
            os.environ.pop("UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR", None)
        else:
            os.environ["UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR"] = previous
    receipt = inspect(source, log, crcs)
    receipt["observed_from_same_windows_executable"] = sha256(args.exe.read_bytes())
    receipt["source_script_sha256"] = route_sha
    receipt["short_2P_route_source_bound"] = route_sha == SHORT_2P_SCRIPT_CRLF_SHA256
    receipt["short_2P_guest_full_CRC_source_bound"] = (
        receipt["actual_native_guest_CRC_sha256"] == SHORT_2P_GUEST_CRC_SHA256)
    (args.out / "qa08-windows-source-result.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # The archived full guest SHA belongs to the before-RF017 generated-core
    # epoch. Preserve its observed mismatch, never silently rewrite that
    # evidence and never use 4 matching pictures as guest parity.
    receipt["historical_pre_RF017_guest_transcript_sha256"] = SHORT_2P_GUEST_CRC_SHA256
    receipt["integrated_RF017_guest_differs_from_historical_archive"] = (
        receipt["actual_native_guest_CRC_sha256"] != SHORT_2P_GUEST_CRC_SHA256)
    (args.out / "qa08-windows-source-result.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Observer OFF in a second clean native Windows process, independent save
    # and framedumps, but identical executable, ROM, input route and RF-017
    # guest. Full per-frame transcript must match; do NOT patch expected hash.
    previous_capture = os.environ.pop("UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR", None)
    try:
        control_crcs, control_log = run_route(
            args.exe.resolve(), args.rom.resolve(), args.script.resolve(),
            args.out / "independent-control", pause=False,
            video=args.video, timeout=args.timeout)
    finally:
        if previous_capture is not None:
            os.environ["UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR"] = previous_capture
    # Keep both *real* 2473-record transcripts for CPU-lane frame bisect.
    for name, values in (("observed", crcs), ("independent-control", control_crcs)):
        (args.out / f"guest-crcs-{name}.txt").write_text(
            "\n".join(x.lower() for x in values) + "\n", encoding="ascii")
    try:
        control = check_current_core_control(route_sha, crcs, control_crcs)
        receipt.update(control)
        receipt["independent_second_real_windows_process"] = True
        receipt["independent_observer_disabled"] = True
    finally:
        (args.out / "qa08-windows-source-result.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if not receipt["all_four_countdown_and_moving_2P_original_source_exact"]:
        raise SystemExit(
            "QA08_WINDOWS_2P_PPU_NOT_ACCEPTED missing or divergent genuine "
            "countdown/three moving 256x224 original-source frames; inspect "
            "source-result.json without guessing alignment or ignoring pixels")
    print("QA08_WINDOWS_2P_PPU full_original_256x224_4frames_exact=1 "
          "same_RF017_PE_independent_process_guest_2473_exact=1 "
          "legacy_pre_RF017_guest_not_rebased=1 release_approved=0")


if __name__ == "__main__":
    main()
