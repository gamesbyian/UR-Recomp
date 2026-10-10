#!/usr/bin/env python3
"""Measure real 4x native P1-only guarded coverage without unsafe OBJ bypass.

This does not certify P2 depth, Remastered race appearance or release; even a
valid positive is merely a candidate for manual visual and source review.
The existing 2P original guest route supplies a separate identical CRC stream.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

if __package__:
    from tools.check_baldosa_physical_4k_capture import read_pam
else:
    from check_baldosa_physical_4k_capture import read_pam

GO = re.compile(r"^script f=(\d+) dump go ok$", re.M)
GATE = re.compile(r"^UR_RACER_HD_CENSUS frame=(\d+) phase=gate status=(original|armed) reason=([a-z0-9-]+)$", re.M)
PRESENT = re.compile(r"^UR_RACER_HD_CENSUS frame=(\d+) phase=present status=(original|hd) reason=([a-z0-9-]+)$", re.M)
CHANGE = re.compile(r"^UR_RACER_HD_PIXEL_CHANGE frame=(\d+) source_instances=(\d+) changed_from_underlay=([01])$", re.M)
PAINT = re.compile(r"^UR_BALDOSA_NATIVE_PAINT frame=(\d+) raster=(\d+)x(\d+) pitch=(\d+) top_changed=(\d+) bottom_changed=(\d+)$", re.M)
NAME = re.compile(r"ur-baldosa-frame-(\d{6})\.pam\Z")
RACE_FRAMES = 2473


def assess(base_crc: Path, trial_crc: Path, log: Path,
           captures: Path) -> dict:
    baseline, candidate = base_crc.read_bytes().splitlines(), trial_crc.read_bytes().splitlines()
    if len(baseline) != RACE_FRAMES or baseline != candidate:
        raise ValueError("full independent 2473-frame guest CRC mismatch")
    text = log.read_text(encoding="utf-8", errors="replace")
    if "UR_RACER_HD_UNSAFE_LEGACY_FIXTURE" in text or (
        "UR_BALDOSA_HD_SOURCE_ART_FIXTURE" in text
    ):
        raise ValueError("unsafe archival fixture present in production-guarded trial")
    go = [int(v) for v in GO.findall(text)]
    if len(go) != 1 or not (0 < go[0] < RACE_FRAMES):
        raise ValueError("missing independent scripted native GO route marker")
    started = go[0]
    gates = [(int(f), status, why) for f, status, why in GATE.findall(text)]
    presents = [(int(f), status, why) for f, status, why in PRESENT.findall(text)]
    if len(gates) < RACE_FRAMES // 2 or not presents:
        raise ValueError("missing actual guest gate / host presentation census")
    p1_armed = {f for f, status, why in gates if status == "armed" and why == "p1-only"}
    p1_presented = {f for f, status, why in presents if status == "hd" and why == "p1-only"}
    if not p1_presented <= p1_armed:
        raise ValueError("host reported P1-only HD without a matching guarded guest admission")
    changes = {int(f): (int(n), int(delta)) for f, n, delta in CHANGE.findall(text)}
    paint = {int(f): (int(w), int(h), int(pitch), int(top), int(bottom))
             for f, w, h, pitch, top, bottom in PAINT.findall(text)}
    after_go_armed = sorted(f for f in p1_armed if f > started)
    after_go_presented = sorted(f for f in p1_presented if f > started)
    evidenced = sorted(
        f for f in after_go_presented
        if changes.get(f, (0, 0))[0] > 0
        and changes.get(f, (0, 0))[1] == 1
        and f in paint and paint[f][0:2] == (1024, 896)
        and paint[f][2] >= 4096
        and (paint[f][3] > 0 or paint[f][4] > 0)
    )
    captured = []
    for file in sorted(captures.glob("ur-baldosa-frame-*.pam")):
        match = NAME.fullmatch(file.name)
        if not match:
            raise ValueError("untrusted / malformed native authored capture filename")
        frame = int(match[1])
        if frame not in p1_presented:
            raise ValueError("native captured HD without guarded host present")
        w, h, pixels = read_pam(file)
        if (w, h) != (1024, 896):
            raise ValueError("native authored capture is not actual 4x density")
        captured.append({
            "guest_frame": frame,
            "sha256": hashlib.sha256(pixels).hexdigest(),
            "actual_raster": [w, h],
            "pixel_changed_from_underlay": changes.get(frame, (0, 0))[1] == 1,
            "after_scripted_go": frame > started,
        })
    # Logs without the actual native composited PAM cannot prove any
    # presented authored pixel, however plausible the telemetry looks.
    witnessed = sorted(
        set(evidenced) & {
            row["guest_frame"] for row in captured
            if row["pixel_changed_from_underlay"] and row["after_scripted_go"]
        }
    )
    before = Counter(why for frame, status, why in gates
                     if frame > started and status == "original")
    return {
        "schema_version": 1,
        "status": ("guarded-p1-host-art-observed" if witnessed
                   else "guarded-p1-host-art-unproven"),
        "native_guest_frames_crc_equal": len(baseline),
        "scripted_go_guest_frame": started,
        "post_go_p1_armed_guest_frames": len(after_go_armed),
        "post_go_p1_hd_presented_guest_frames": len(after_go_presented),
        "post_go_p1_host_pixel_change_witness_frames": witnessed,
        "post_go_original_fallback_reasons": dict(sorted(before.items())),
        "native_authored_4x_captures": captured,
        "unsafe_overlap_bypass_used": False,
        "release_hd_admission": False,
        "p2_stock_occlusion_parity_proven": False,
        "production_player_appearance_accepted": False,
        "limits": (
            "P1-only admission uses the existing split-alias and P2 rectangle "
            "occlusion guards. Post-capture underlay changes can indicate "
            "native authored P1 pixels but cannot prove full P2 stock depth, "
            "moving-gameplay aesthetic consistency or safe product defaults. "
            "Never enable this diagnostic in shipped graphics options based "
            "solely on this report."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-crc", required=True, type=Path)
    p.add_argument("--trial-crc", required=True, type=Path)
    p.add_argument("--log", required=True, type=Path)
    p.add_argument("--captures", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    x = p.parse_args()
    result = assess(x.baseline_crc, x.trial_crc, x.log, x.captures)
    x.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("UR_BALDOSA_P1_GUARDED_COVERAGE "
          f"status={result['status']} "
          f"post_go_armed={result['post_go_p1_armed_guest_frames']} "
          f"post_go_present={result['post_go_p1_hd_presented_guest_frames']} "
          f"pixel_witnesses={len(result['post_go_p1_host_pixel_change_witness_frames'])} "
          f"original_reasons={result['post_go_original_fallback_reasons']}")


if __name__ == "__main__":
    main()
