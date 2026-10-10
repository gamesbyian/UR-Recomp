#!/usr/bin/env python3
"""Conservative native 1P 4x Racer-HD trial from existing guarded presenter.

Exact independently executed full 1P guest CRC, guest/host admission and real
source-derived dense pixels are required. The bounded moving-race observation
window is NOT an original finish or phase/state oracle, and no player option
is enabled by this check. Does not broaden 2P or 342-wide sprite admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

if __package__:
    from tools.check_baldosa_guarded_p1_coverage import (
        GATE, PRESENT, CHANGE, PAINT, NAME,
    )
    from tools.check_baldosa_physical_4k_capture import read_pam
else:
    from check_baldosa_guarded_p1_coverage import (
        GATE, PRESENT, CHANGE, PAINT, NAME,
    )
    from check_baldosa_physical_4k_capture import read_pam

GUEST_FRAMES = 5447
OBSERVED_MOVING_WINDOW = (1800, 2450)


def assess(stock_crc: Path, trial_crc: Path, trial_log: Path,
           captures: Path) -> dict:
    baseline, candidate = (
        stock_crc.read_bytes().splitlines(), trial_crc.read_bytes().splitlines()
    )
    if len(baseline) != GUEST_FRAMES or baseline != candidate:
        raise ValueError("independent complete native 1P 5447-frame CRC mismatch")
    text = trial_log.read_text(encoding="utf-8", errors="replace")
    if ("UR_RACER_HD_UNSAFE_LEGACY_FIXTURE" in text or
        "UR_BALDOSA_HD_SOURCE_ART_FIXTURE" in text):
        raise ValueError("unsafe overlap bypass disqualifies guarded 1P visuals")
    gates = [(int(f), stat, reason) for f, stat, reason in GATE.findall(text)]
    presents = [(int(f), stat, reason) for f, stat, reason in PRESENT.findall(text)]
    if len(gates) != GUEST_FRAMES or len({f for f, _, _ in gates}) != GUEST_FRAMES:
        raise ValueError("incomplete/duplicated genuine 1P guest-gate census")
    if not presents:
        raise ValueError("no real host presented-frame observations")
    low, high = OBSERVED_MOVING_WINDOW
    eligible = [(f, stat, reason) for f, stat, reason in gates if low <= f <= high]
    guarded = {f for f, stat, reason in eligible if stat == "armed" and reason == "p1-only"}
    full = {f for f, stat, reason in eligible if stat == "armed" and reason == "full-pair"}
    presented = {f for f, stat, reason in presents if low <= f <= high and
                 stat == "hd" and reason == "p1-only"}
    full_presented = {f for f, stat, reason in presents if low <= f <= high and
                      stat == "hd" and reason == "full-pair"}
    if not presented <= guarded or not full_presented <= full:
        raise ValueError("source-unarmed guest frame appeared in 1P HD host output")
    change = {int(f): (int(instances), int(delta))
              for f, instances, delta in CHANGE.findall(text)}
    paints = {int(f): (int(w), int(h), int(pitch), int(top), int(bottom))
              for f, w, h, pitch, top, bottom in PAINT.findall(text)}
    captured = []
    for file in sorted(captures.glob("ur-baldosa-frame-*.pam")):
        marker = NAME.fullmatch(file.name)
        if not marker:
            raise ValueError("uncertain native 1P authored frame provenance")
        frame = int(marker[1])
        if frame not in presented and frame not in full_presented:
            raise ValueError("unarmed guest frame gained an authored 1P PAM")
        w, h, pixels = read_pam(file)
        if (w, h) != (1024, 896):
            raise ValueError("native 1P capture is not real 4x source density")
        metric = paints.get(frame)
        nonzero = bool(metric and metric[:2] == (w, h) and metric[2] >= 4096
                       and (metric[3] > 0 or metric[4] > 0))
        changed = change.get(frame, (0, 0))[0] > 0 and change.get(frame, (0, 0))[1] == 1
        captured.append({
            "guest_frame": frame, "rgba_sha256": hashlib.sha256(pixels).hexdigest(),
            "physical_native_raster": [w, h], "source_painted": nonzero and changed,
            "source_paint_rect_change_top_bottom": list(metric[3:5]) if metric else [],
        })
    qualifying = [
        entry["guest_frame"] for entry in captured
        if entry["source_painted"] and
        (entry["guest_frame"] in presented or entry["guest_frame"] in full_presented)
    ]
    reasons = Counter(reason for _, status, reason in eligible if status == "original")
    return {
        "schema_version": 1,
        "status": ("safe-one-player-4x-art-observed" if qualifying
                   else "safe-one-player-4x-art-unproven"),
        "full_guest_crc_match": True,
        "guest_crc_frames": len(baseline),
        "moving_observation_window": [low, high],
        "one_player_phase_independently_accepted": False,
        "source_guarded_p1_only_guest_admissions": len(guarded),
        "source_guarded_full_pair_guest_admissions": len(full),
        "real_p1_only_hd_host_guest_frames": len(presented),
        "real_full_pair_hd_host_guest_frames": len(full_presented),
        "real_source_changed_4x_capture_frames": qualifying,
        "original_fallback_reasons": dict(sorted(reasons.items())),
        "native_4x_pam_sha256": captured,
        "unsafe_overlap_fixture": False,
        "widescreen_hd_admission": False,
        "production_graphics_accepted": False,
        "limits": (
            "Only an existing fixed-256 bounded 1P route at frames1800-2450. "
            "No 342-wide HD or source-visible post-removal P2 parity. "
            "A positive 4x capture is evidence of authored host pixels, not "
            "a finished Remastered race, hardware/window acceptance or "
            "release option. No guest or renderer ownership changes."
        ),
    }


def main() -> None:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--stock-crc", type=Path, required=True)
    a.add_argument("--trial-crc", type=Path, required=True)
    a.add_argument("--trial-log", type=Path, required=True)
    a.add_argument("--captures", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    x = a.parse_args()
    outcome = assess(x.stock_crc, x.trial_crc, x.trial_log, x.captures)
    x.out.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    print("UR_BALDOSA_SAFE_1P_4X "
          f"status={outcome['status']} "
          f"guarded={outcome['source_guarded_p1_only_guest_admissions']} "
          f"presented={outcome['real_p1_only_hd_host_guest_frames']} "
          f"source_pams={len(outcome['real_source_changed_4x_capture_frames'])}")


if __name__ == "__main__":
    main()
