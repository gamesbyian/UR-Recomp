#!/usr/bin/env python3
"""Read-only 1P first-party authored-HD availability in the actual Baldosa race.

Count distinct guest frames and REAL sparse desktop-present frames separately.
Never promote registration/OAM admission or a fallback screenshot to HD. Retain
the complete native guest CRC comparison and source-visible 4x pixel witness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from tools.measure_racer_hd_live_draws import analyze
    from tools.check_baldosa_physical_4k_capture import read_pam
except ModuleNotFoundError:
    from measure_racer_hd_live_draws import analyze
    from check_baldosa_physical_4k_capture import read_pam

FRAME_RE = re.compile(r"^ur-baldosa-frame-(\d{6})\.pam$")
RACE_ENTRY = re.compile(r"(?m)^script f=(\d+) until 00E1F ok after \d+ frames$")
ROUTE_END = re.compile(r"(?m)^script f=(\d+) dump end ok$")
HD_PIXEL_CHANGE = re.compile(
    r"(?m)^UR_RACER_HD_PIXEL_CHANGE frame=(\d+) source_instances=(\d+) "
    r"changed_from_underlay=([01])$"
)
PAINT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_PAINT frame=(\d+) raster=(\d+)x(\d+) "
    r"pitch=(\d+) top_changed=(\d+) bottom_changed=(\d+)$"
)


def assess(base_crc: Path, candidate_crc: Path, candidate_log: Path,
           captures: Path) -> dict:
    stock, trial = base_crc.read_bytes().splitlines(), candidate_crc.read_bytes().splitlines()
    if not stock or stock != trial:
        raise ValueError("independently executed native 1P guest CRC mismatch")
    log = candidate_log.read_text(encoding="utf-8", errors="replace")
    if "UR_RACER_HD_UNSAFE_LEGACY_FIXTURE" in log or (
        "UR_BALDOSA_HD_SOURCE_ART_FIXTURE" in log
    ):
        raise ValueError("unsafe archival P1/P2 overlap-bypass fixture is forbidden")
    entered, ended = RACE_ENTRY.findall(log), ROUTE_END.findall(log)
    if len(entered) != 1 or len(ended) != 1:
        raise ValueError("actual 1P native script lacks unique race/terminal markers")
    start, end = int(entered[0]), int(ended[0])
    if start <= 0 or end != len(stock) or end <= start + 300:
        raise ValueError("native 1P route frame/progression provenance incomplete")
    report = analyze(log, from_frame=start + 1, to_frame=end)
    m = report["measurement"]
    if m["guest_frames_observed"] != end - start:
        raise ValueError("incomplete actual 1P candidate guest gates")
    hd_frames = set(m["hd_guest_frames"])
    # Preserve absolute source provenance, but this accepted measurement
    # deliberately begins AFTER the authentic race-script entry. The same
    # native guest can have legitimate HD menu/countdown callbacks before
    # the scoped race window; never mistake those for race HD or a defect.
    delta = {
        int(f): (int(s), v == "1")
        for f, s, v in HD_PIXEL_CHANGE.findall(log)
        if start < int(f) <= end
    }
    paints = {
        int(f): tuple(map(int, (w, h, pitch, top, bottom)))
        for f, w, h, pitch, top, bottom in PAINT.findall(log)
        if start < int(f) <= end
    }
    if not set(delta) <= hd_frames or not set(paints) <= hd_frames:
        raise ValueError("post-entry HD pixel change without native host admission")
    # Source 1P is in top viewport; default 2P fallback must not borrow
    # arbitrary bottom differences as evidence of actual P1 Remastered.
    real_p1 = sorted(f for f in hd_frames if f in paints
                     and paints[f][0:2] == (1024, 896)
                     and paints[f][2] >= 4096
                     and paints[f][3] > 0
                     and delta.get(f, (0, False))[0] > 0
                     and delta[f][1])
    images = []
    for file in sorted(captures.glob("ur-baldosa-frame-*.pam")):
        match = FRAME_RE.fullmatch(file.name)
        if match is None:
            raise ValueError("untrusted or malformed native screenshot name")
        f = int(match[1])
        if f not in hd_frames:
            raise ValueError("captured 1P HD native screenshot has no actual host presentation")
        w, h, raw = read_pam(file)
        if (w, h) != (1024, 896):
            raise ValueError("native authored 1P image is not actual 4x density")
        images.append({
            "frame": f, "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "dimensions": [w, h], "after_race_entry": f > start,
            "source_visible_p1": f in real_p1,
        })
    source_pixels = sorted(set(real_p1) & {
        i["frame"] for i in images if i["source_visible_p1"]
    })
    return {
        "schema_version": 1,
        "status": ("guarded-1p-real-art-observed" if source_pixels else
                   "guarded-1p-real-art-unproven"),
        "native_guest_crc_equal": len(stock),
        "native_1p_race_entry": start,
        "native_1p_route_end": end,
        "race_guest_frames_scoped": m["guest_frames_observed"],
        "race_host_presents_observed": m["host_present_calls"],
        "race_guest_hd_armed": m["capture_armed_guest_frames"],
        "race_hd_host_presents": m["hd_present_calls"],
        "guest_fallback_reasons": m["gate_fallback_reasons"],
        "real_p1_pixel_difference_frames": real_p1,
        "raw_native_4x_art_images": images,
        "verified_4x_p1_visible_image_frames": source_pixels,
        "unsafe_fixture_used": False,
        "product_beta_approved": False,
        "widescreen_hd_approved": False,
        "racer_p2_foreground_authorized": False,
        "limits": (
            "Real first-party 1P authored pixel coverage only in fixed "
            "256x224 host rendering; cannot grant widened-342 HD sprite "
            "replacement, original-emulator depth parity, a completed event "
            "or the integrated Windows Modern graphics path."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline-crc", required=True, type=Path)
    ap.add_argument("--candidate-crc", required=True, type=Path)
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--captures", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    x = ap.parse_args()
    report = assess(x.baseline_crc, x.candidate_crc, x.log, x.captures)
    x.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("UR_BALDOSA_GUARDED_1P_HD "
          f"status={report['status']} "
          f"guest={report['race_guest_frames_scoped']} "
          f"present={report['race_host_presents_observed']} "
          f"hd_presents={report['race_hd_host_presents']} "
          f"visible_hd_images={len(report['verified_4x_p1_visible_image_frames'])} "
          f"fallbacks={report['guest_fallback_reasons']}")


if __name__ == "__main__":
    main()
