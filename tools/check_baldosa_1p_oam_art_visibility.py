#!/usr/bin/env python3
"""Rank native 1P Remastered source states by *possible* source OBJ screen geometry.

All observations come from the same independent 5,447-frame guest route.
An on-screen 64x64 source OAM rectangle is only a GEOMETRIC upper bound:
it cannot prove emitted opaque OBJ pixels, final BG priority or authorized HD.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

try:
    from tools.check_baldosa_1p_art_state_worklist import (
        assess as assess_semantics, LINE as STATE, RACE, END,
    )
except ModuleNotFoundError:
    from check_baldosa_1p_art_state_worklist import (
        assess as assess_semantics, LINE as STATE, RACE, END,
    )

OAM = re.compile(
    r"^UR_RACER_HD_1P_OAM frame=(\d+) source_ready=([01]) "
    r"top_x=(-?\d+) top_y=(\d+) top_tile=([0-9A-F]{2}) top_large=([01]) top_geom=([01]) "
    r"bottom_x=(-?\d+) bottom_y=(\d+) bottom_tile=([0-9A-F]{2}) bottom_large=([01]) bottom_geom=([01]) "
    r"obsel=([0-9A-F]{2}) rotation=([01]) source_bank=([01]) front_safe=([01])$"
)


def bounds(x: int, y: int, upper: bool) -> bool:
    """Original SNES 9-bit signed X and Y modulo 256, split at line 112."""
    if x < -256 or x > 255 or y < 0 or y > 255:
        return False
    if x >= 256 or x + 64 <= 0:
        return False
    lo, hi = (0, 112) if upper else (112, 224)
    return any(((scanline - y) & 0xFF) < 64
               for scanline in range(lo, hi))


def parse_oam(lines: list[str]) -> dict[int, dict]:
    out = {}
    for line in lines:
        if not line.startswith("UR_RACER_HD_1P_OAM "):
            continue
        m = OAM.fullmatch(line)
        if m is None:
            raise ValueError("malformed source-origin native P1 OAM geometry trace")
        vals = m.groups()
        frame = int(vals[0])
        if frame in out or not 1700 <= frame <= 5150:
            raise ValueError("duplicate or outside-window guest P1 OAM observation")
        ready = vals[1] == "1"
        tx, ty, tt, tlarge, tg = int(vals[2]), int(vals[3]), int(vals[4], 16), vals[5] == "1", vals[6] == "1"
        bx, by, bt, blarge, bg = int(vals[7]), int(vals[8]), int(vals[9], 16), vals[10] == "1", vals[11] == "1"
        obsel, rot, bank, safe = int(vals[12], 16), vals[13] == "1", vals[14] == "1", vals[15] == "1"
        if not ready and (tg or bg or bank or safe):
            raise ValueError("unbound source OAM cannot prove racer visibility")
        if ready and (not (-256 <= tx <= 255 and -256 <= bx <= 255) or
                      not (0 <= ty <= 255 and 0 <= by <= 255)):
            raise ValueError("invalid original SNES nine-bit signed X/Y bounds")
        if ready and (tg != (tlarge and bounds(tx, ty, True)) or
                      bg != (blarge and bounds(bx, by, False))):
            raise ValueError("native original P1 OAM reported impossible on-screen geometry")
        if bank and (not ready or obsel != 0x83 or
                     tt not in (0, 8) or bt not in (0, 8)):
            raise ValueError("invalid source P1 OBJ tile bank or OBSEL")
        if safe and (not bank or rot):
            raise ValueError("unsafe native P2 foreground priority bypass")
        out[frame] = {
            "source_ready": ready, "top_x": tx, "top_y": ty,
            "bottom_x": bx, "bottom_y": by,
            "top_tile": f"{tt:02X}", "bottom_tile": f"{bt:02X}",
            "top_large_64": tlarge, "bottom_large_64": blarge,\n            "top_source_geometry": tg, "bottom_source_geometry": bg,
            "source_bank": bank, "obsel": f"{obsel:02X}",
            "priority_rotated": rot, "conservative_front_safe": safe,
        }
    if not out:
        raise ValueError("no genuine native P1 source OAM traces available")
    return out


def assess(baseline_crc: Path, candidate_crc: Path, native_log: Path) -> dict:
    source = assess_semantics(baseline_crc, candidate_crc, native_log)
    lines = native_log.read_text(encoding="utf-8", errors="replace").splitlines()
    if any("UR_RACER_HD_UNSAFE_LEGACY_FIXTURE enabled=1" in x for x in lines):
        raise ValueError("unsafe original PPU source replacement fixture used")
    race = [int(m[1]) for x in lines if (m := RACE.fullmatch(x))]
    end = [int(m[1]) for x in lines if (m := END.fullmatch(x))]
    if len(race) != 1 or len(end) != 1 or end[0] != 5447:
        raise ValueError("independent native 1P race/end scope unavailable")
    state = {}
    for line in lines:
        if not line.startswith("UR_RACER_HD_1P_STATE "):
            continue
        m = STATE.fullmatch(line)
        if m is None:
            raise ValueError("malformed original 1P semantic source sample")
        f = int(m[1])
        if f in state:
            raise ValueError("duplicate semantic sample")
        state[f] = {
            "semantic": m[2], "primary": m[3], "companion": m[4],
            "selector": m[5], "gate": m[6],
            "registered": m[7] == "1", "art": m[8] == "1",
            "selected": m[9] != "0",
        }
    oam = parse_oam(lines)
    if set(state) != set(oam) or len(state) != source["native_trace_guest_frames"]:
        raise ValueError("source OAM identities cannot cover every original semantic guest frame")
    candidate = [f for f in sorted(state) if race[0] < f <= end[0]]
    if len(candidate) != source["post_milestone_trace_guest_frames"]:
        raise ValueError("source-OAM guest scope disagrees with independently authenticated semantic inventory")
    counts = Counter()
    by_state = defaultdict(lambda: Counter())
    for f in candidate:
        w = state[f]
        p = oam[f]
        shape = ":".join(w[k] for k in ("semantic", "primary", "companion", "selector", "gate"))
        kind = ("missing_art" if not w["art"] else
                "authored_unregistered" if not w["selected"] else "selected_authored")
        visible = p["source_ready"] and p["source_bank"] and (
            p["top_source_geometry"] or p["bottom_source_geometry"])
        safe = visible and p["conservative_front_safe"]
        counts[f"{kind}_total"] += 1
        by_state[shape]["total"] += 1
        by_state[shape][kind] += 1
        if visible:
            counts[f"{kind}_onscreen_geometry_possible"] += 1
            by_state[shape]["onscreen_geometry_possible"] += 1
        if safe:
            counts[f"{kind}_conservative_p1_only_geometry_safe"] += 1
            by_state[shape]["conservative_p1_only_geometry_safe"] += 1
        if not p["source_ready"] or not p["source_bank"]:
            counts[f"{kind}_source_bank_unproven"] += 1
            by_state[shape]["source_bank_unproven"] += 1
        if not p["top_source_geometry"] and not p["bottom_source_geometry"]:
            counts[f"{kind}_original_stock_screen_empty_geometry"] += 1
            by_state[shape]["original_stock_screen_empty_geometry"] += 1
    if counts["missing_art_total"] != source["missing_authored_asset_samples"] or (
        counts["authored_unregistered_total"] != source["registered_art_state_mismatch_samples"]
    ) or counts["selected_authored_total"] != source["registered_state_samples"]:
        raise ValueError("native geometry categories changed independently accepted semantic art totals")
    rankings = [
        {"state": label, **dict(c)}
        for label, c in by_state.items()
        if c["missing_art"] or c["authored_unregistered"]
    ]
    rankings.sort(key=lambda x: (-x.get("onscreen_geometry_possible", 0),
                                 -x.get("total", 0), x["state"]))
    return {
        "schema_version": 1,
        "status": "bounded-native-1p-oam-geometry-worklist",
        "native_guest_crc_equal": 5447,
        "native_post_race_milestone_guest_observations": len(candidate),
        "race_script_milestone": race[0],
        "classification": dict(sorted(counts.items())),
        "top_30_original_source_geometry_caller_states": rankings[:30],
        "unique_missing_or_unregistered_runtime_compositions": len(rankings),
        "new_art_approved": False,
        "source_obj_alpha_visibility_proven": False,
        "untouched_stock_final_bg_priority_proven": False,
        "wide_hd_admitted": False,
        "limits": (
            "READ-ONLY PPU/OAM original screen-intersection upper bound, not "
            "source sprite emission, alpha ownership, final PPU BG/window "
            "priority, camera-shifted 342-wide placement, an independent "
            "original-emulator test or release authorization."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-crc", required=True, type=Path)
    p.add_argument("--candidate-crc", required=True, type=Path)
    p.add_argument("--log", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    report = assess(args.baseline_crc, args.candidate_crc, args.log)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("UR_RACER_HD_1P_OAM_WORKLIST "
          f"guest={report['native_post_race_milestone_guest_observations']} "
          f"art_missing={report['classification'].get('missing_art_total', 0)} "
          f"possible={report['classification'].get('missing_art_onscreen_geometry_possible', 0)} "
          "source_alpha_approved=0 wide_hd_admitted=0")


if __name__ == "__main__":
    main()
