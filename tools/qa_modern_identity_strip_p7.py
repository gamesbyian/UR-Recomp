#!/usr/bin/env python3
"""Source/PE-bound real SDL P7 audit of Modern racer identity contrast (#2131).

The native root draws a 320/240-wide panel at (11/8, 10), with an opaque
stock #181818 identity strip and stock-family #C8C8C8 label. Sample every
logical-pixel centre after actual 7:6 PAR SDL nearest-neighbour presentation.
This verifies a *real final output*, not a synthetic presenter callback.
No human visual, alpha-composited monitor, original-game or release approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

try:
    from tools import qa_modern_visual_diagnostics as visual
    from tools.qa_modern_visual_native_contrast import contrast_ratio
except ModuleNotFoundError:  # direct script invocation
    import qa_modern_visual_diagnostics as visual
    from qa_modern_visual_native_contrast import contrast_ratio

BG = (24, 24, 24)
FG = (200, 200, 200)
EXPECTED = ((342, (1280, 720)), (256, (1024, 768)))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit_frame(frame: visual.Frame, logical_width: int) -> dict:
    """Reject missing strip, checker bleed, glyph loss and clipped identity."""
    if logical_width not in (256, 342):
        raise ValueError("unsupported native logical width")
    panel_width = 320 if logical_width == 342 else 240
    root_x, root_y = (logical_width - panel_width) // 2, 10
    x0, x1 = root_x + 5, root_x + panel_width - 5
    y0, y1 = root_y + 31, root_y + 49
    mapping = visual.mapping(logical_width, 224, frame.width, frame.height)
    fg_points, bg_count, foreign = [], 0, {}
    for ly in range(y0, y1):
        oy = int(mapping.vy + (ly + 0.5) * mapping.sy)
        for lx in range(x0, x1):
            ox = int(mapping.vx + (lx + 0.5) * mapping.sx)
            rgb = frame.rgb(ox, oy)
            if rgb == FG:
                fg_points.append((lx, ly))
            elif rgb == BG:
                bg_count += 1
            else:
                foreign[rgb] = foreign.get(rgb, 0) + 1
    bounds = [min(x for x, _ in fg_points), min(y for _, y in fg_points),
              max(x for x, _ in fg_points) + 1, max(y for _, y in fg_points) + 1] if fg_points else None
    # The 8px host fallback starts at (root+8, root+36). Preserve both
    # text margins; a right-clipped name must not be called visually valid.
    within_glyph_bounds = bool(bounds) and (
        root_x + 8 <= bounds[0] and bounds[2] < x1 and
        root_y + 36 <= bounds[1] and bounds[3] <= root_y + 44)
    checks = {
        "opaque_strip_no_checker_bleed": not foreign,
        "visible_identity_glyphs": len(fg_points) >= 25,
        "solid_backing_observed": bg_count >= 100,
        "identity_not_clipped": within_glyph_bounds,
        "source_rgb_contrast_at_least_4_5": contrast_ratio(FG, BG) >= 4.5,
    }
    return {
        "logical_width": logical_width,
        "output": [frame.width, frame.height],
        "identity_strip_logical_rect": [x0, y0, x1, y1],
        "glyph_bbox_logical": bounds,
        "foreground_rgb": list(FG), "backing_rgb": list(BG),
        "foreground_logical_pixels": len(fg_points),
        "backing_logical_pixels": bg_count,
        "unexpected_logical_pixels": sum(foreign.values()),
        "unexpected_rgb_examples": [{"rgb": list(rgb), "count": count}
                                    for rgb, count in sorted(foreign.items(), key=lambda v: -v[1])[:5]],
        "source_rgb_contrast": round(contrast_ratio(FG, BG), 4),
        "checks": checks, "pass": all(checks.values()),
    }



def audit_observed_frame(frame: visual.Frame, expected_logical_width: int) -> dict:
    """Measure the actual source grid before sampling the identity strip.

    A 256-wide root stretched to a 1280x720 drawable must not be misreported
    as 342-wide checkerboard bleed. Keep the width mismatch as a failing
    product check while reporting the real 256-wide strip's pixel integrity.
    """
    detected = visual.detect_logical(frame, (256, 342))
    widths = detected["consistent_widths"]
    if len(widths) != 1:
        raise ValueError("ambiguous native source width in final SDL P7")
    observed_width = widths[0]
    report = audit_frame(frame, observed_width)
    report["expected_logical_width"] = expected_logical_width
    report["observed_logical_width"] = observed_width
    report["logical_width_nonuniform_fraction"] = detected["nonuniform_fraction"]
    report["checks"]["expected_logical_width"] = observed_width == expected_logical_width
    report["pass"] = all(report["checks"].values())
    return report


def audit_capture(directory: Path, logical_width: int, expected_output: tuple[int, int],
                  expected_source_sha: str) -> dict:
    receipt = json.loads((directory / "readback-receipt.json").read_text())
    raw = (directory / "probe_first" / "actual-sdl-drawable.pam").read_bytes()
    png = (directory / "actual-sdl-drawable.png").read_bytes()
    if (receipt.get("source_sha") != expected_source_sha or
        receipt.get("native_semantic_route") != "root-quit" or
        receipt.get("execution_mode") != "modern" or
        receipt.get("native_process_exit") != 0 or
        receipt.get("SDL_driver") != "windows" or
        tuple(receipt.get("actual_sdl_renderer_output", ())) != expected_output or
        receipt.get("p7_sha256") != sha256(raw) or
        receipt.get("png_sha256") != sha256(png)):
        raise ValueError(f"unqualified Windows SDL readback receipt: {directory}")
    frame = visual.Frame(raw)
    converted = visual.Frame(png)
    if (frame.width, frame.height) != expected_output or frame.rgba != converted.rgba:
        raise ValueError(f"P7/PNG final SDL pixels differ: {directory}")
    report = audit_observed_frame(frame, logical_width)
    report.update({"p7_sha256": sha256(raw), "png_sha256": sha256(png),
                   "exe_sha256": receipt["exe_sha256"],
                   "source_sha": receipt["source_sha"],
                   "capture": directory.name})
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wide", type=Path, required=True)
    ap.add_argument("--compact", type=Path, required=True)
    ap.add_argument("--expected-source-sha", required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        if len(a.expected_source_sha) != 40 or any(c not in "0123456789abcdef" for c in a.expected_source_sha):
            raise ValueError("expected source must be lowercase 40-hex Git SHA")
        captures = [audit_capture(a.wide, *EXPECTED[0], a.expected_source_sha),
                    audit_capture(a.compact, *EXPECTED[1], a.expected_source_sha)]
        if captures[0]["exe_sha256"] != captures[1]["exe_sha256"]:
            raise ValueError("different Windows PE used for wide and compact captures")
        result = {"schema": "ur-modern-identity-final-sdl-p7-v1",
                  "source_sha": a.expected_source_sha,
                  "exe_sha256": captures[0]["exe_sha256"],
                  "captures": captures, "pass": all(c["pass"] for c in captures),
                  "human_visual_approved": False, "physical_monitor_approved": False,
                  "original_guest_equivalence_approved": False, "release_gate_credit": 0}
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
