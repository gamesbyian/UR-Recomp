#!/usr/bin/env python3
"""Derive and run the machine-checkable part of a Modern visual acceptance case.

For each case in analysis/modern-visual-acceptance-matrix.json this fixes the
scene-qualified native logical canvas (fixed Modern menu scenes -> 256x224,
wide live-world scenes -> 342x224) and the
checks a final-SDL capture of that case can be held to without a human:

* output size equals the case's `pixels` (exact mode/geometry evidence);
* exactly one native logical width explains the frame (a genuine 342-wide or
  256-wide source, not a stretched other one) -- see `detect_logical`;
* for Modern UI screens drawn with the stock palette (root, profiles,
  multiplayer, practice, options, records): stock UI text stays inside the
  action-safe region without touching the viewport edge, and the selection
  marker forms exactly one focus bar where the screen has a focus cursor.

Title, transition and Authentic cases use other palettes, so they get the
size and logical-width checks only. A pass is a measurement. It is never
human art approval, physical-display acceptance or original-game parity,
and `release_gate_credit` is always 0.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from tools import qa_modern_visual_diagnostics as d
except ModuleNotFoundError:
    import qa_modern_visual_diagnostics as d

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "analysis/modern-visual-acceptance-matrix.json"
LOGICAL = {"16:9": 342, "4:3": 256}
UI_SCREENS = frozenset({"root", "profiles", "multiplayer", "practice",
                        "options", "records"})
# Stock Modern UI text colours (modern_stock_menu_palette / grammar tokens).
UI_TEXT = ((255, 255, 255), (200, 200, 200), (248, 248, 0), (160, 208, 248),
           (136, 200, 240), (240, 160, 136))
FOCUS_MARKERS = ((160, 208, 248), (136, 200, 240), (240, 160, 136))
# Screens where a cursor/selection is the point of the state.
FOCUS_STATES = frozenset({"normal", "selection-moved", "stale-profile",
                          "no-profile", "existing-profiles", "locked-course",
                          "p1-p2-named", "no-records", "earned-1p",
                          "earned-2p", "display-apply-refused", "focus-lost"})


def load_cases(path: Path = MATRIX) -> dict:
    return {c["id"]: c for c in json.loads(path.read_text())["cases"]}


def plan(case: dict) -> dict:
    # Fixed Modern menu scenes keep their 256px source even in 16:9 SDL
    # windows. The aspect field describes the output requirement, not an
    # instruction to widen the menu raster (see #2534 Windows P7 evidence).
    lw = (256 if case["mode"] == "modern" and case["screen"] in UI_SCREENS
          else LOGICAL[case["aspect"]])
    ui = case["mode"] == "modern" and case["screen"] in UI_SCREENS
    return {"case": case["id"], "output": list(case["pixels"]),
            "logical": [lw, 224],
            "check_clip": ui,
            "check_focus": ui and case["state"] in FOCUS_STATES
                           and case["screen"] != "records"}


def evaluate(case: dict, frame: d.Frame, require_ring: bool = False) -> dict:
    p = plan(case)
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    add("output-size", [frame.width, frame.height] == p["output"],
        {"expected": p["output"], "observed": [frame.width, frame.height]})
    det = d.detect_logical(frame, (256, 342))
    add("logical-width", det["consistent_widths"] == [p["logical"][0]],
        {"expected": p["logical"][0], "nonuniform": det["nonuniform_fraction"]})
    if p["check_clip"]:
        try:
            clip = d.clip_audit(frame, *p["logical"], list(UI_TEXT), "action")
            add("action-safe", clip["pass"],
                {"bbox": clip["content_bbox_logical"],
                 "edge_pixels": clip["viewport_edge_pixels"]})
        except ValueError as exc:
            add("action-safe", False, {"error": str(exc)})
    if p["check_focus"]:
        m = d.mapping(*p["logical"], frame.width, frame.height)
        bars = [d.focus_audit(frame, mk, m.sx, scale_y=m.sy)["bars"]
                for mk in FOCUS_MARKERS]
        total = sum(len(b) for b in bars)
        add("single-focus-bar", total == 1, {"bars_by_marker": bars})
        if total == 1:
            bar = next(b[0] for b in bars if b)
            ring = d.focus_ring_audit(frame, bar, m)
            # Advisory unless required: captures made before the shared
            # two-tone ring existed (archived runs) must not turn red.
            add("focus-ring", ring["pass"] or not require_ring,
                {"present": ring["pass"], "required": require_ring,
                 "samples": ring["samples"]})
    return {"schema": "ur-modern-visual-case-v1", "case": case["id"],
            "input_sha256": frame.sha256, "checks": checks,
            "pass": all(c["pass"] for c in checks),
            "human_visual_approved": False, "physical_monitor_approved": False,
            "original_guest_equivalence_approved": False,
            "release_gate_credit": 0}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case")
    ap.add_argument("frame", type=Path)
    ap.add_argument("--expect-sha256")
    ap.add_argument("--matrix", type=Path, default=MATRIX)
    ap.add_argument("--require", action="store_true")
    ap.add_argument("--require-ring", action="store_true",
                    help="fail frames lacking the shared two-tone focus ring")
    a = ap.parse_args(argv)
    try:
        cases = load_cases(a.matrix)
        if a.case not in cases:
            raise ValueError(f"unknown case {a.case!r}")
        rep = evaluate(cases[a.case], d.load(a.frame, a.expect_sha256),
                       a.require_ring)
    except (OSError, ValueError, KeyError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(rep, indent=2))
    return 2 if a.require and not rep["pass"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
