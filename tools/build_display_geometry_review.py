#!/usr/bin/env python3
"""Build a deterministic display-geometry review report from canonical BMP captures.

This is presentation-only analysis. It never mutates guest state or runtime output.
Candidates remain hypotheses until title-specific visual evidence promotes one.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

try:
    from tools.compare_ui_frames import load_bmp
    from tools.widescreen_probe import derive_symmetric_margin, parse_ratio
except ModuleNotFoundError:
    from compare_ui_frames import load_bmp
    from widescreen_probe import derive_symmetric_margin, parse_ratio


def candidate_report(
    *,
    width: int,
    height: int,
    candidate: dict[str, Any],
    capacity_margin: int = 64,
    granularity: int = 8,
) -> dict[str, Any]:
    crop_top = int(candidate.get("crop_top", 0))
    crop_bottom = int(candidate.get("crop_bottom", 0))
    if crop_top < 0 or crop_bottom < 0 or crop_top + crop_bottom >= height:
        raise ValueError(f"invalid crop for {height}-line framebuffer")
    active_height = height - crop_top - crop_bottom
    par = parse_ratio(str(candidate["pixel_aspect"]))
    target = parse_ratio(str(candidate.get("target_aspect", "16:9")))
    derived = derive_symmetric_margin(
        base_logical_width=width,
        logical_height=active_height,
        target_aspect=target,
        pixel_aspect=par,
        granularity=granularity,
        capacity_margin=capacity_margin,
    )
    display_aspect = Fraction(width) * par / active_height
    return {
        "id": str(candidate["id"]),
        "label": str(candidate.get("label", candidate["id"])),
        "status": str(candidate.get("status", "provisional")),
        "pixel_aspect": str(candidate["pixel_aspect"]),
        "target_aspect": str(candidate.get("target_aspect", "16:9")),
        "crop_top": crop_top,
        "crop_bottom": crop_bottom,
        "active_logical_height": active_height,
        "stock_display_aspect": {
            "numerator": display_aspect.numerator,
            "denominator": display_aspect.denominator,
            "decimal": float(display_aspect),
        },
        "derived_16x9": derived,
    }


def build_report(
    capture_paths: list[Path],
    candidates: list[dict[str, Any]],
    *,
    capacity_margin: int = 64,
    granularity: int = 8,
) -> dict[str, Any]:
    captures = []
    geometry: tuple[int, int] | None = None
    for path in capture_paths:
        width, height, _ = load_bmp(path)
        if geometry is None:
            geometry = (width, height)
        elif geometry != (width, height):
            raise ValueError(
                f"mixed framebuffer geometry: {geometry[0]}x{geometry[1]} vs "
                f"{width}x{height} at {path}"
            )
        captures.append({
            "tag": path.name.removesuffix(".fb.bmp"),
            "path": str(path),
            "width": width,
            "height": height,
        })
    if not captures or geometry is None:
        raise ValueError("at least one canonical framebuffer capture is required")
    width, height = geometry
    rows = [
        candidate_report(
            width=width,
            height=height,
            candidate=candidate,
            capacity_margin=capacity_margin,
            granularity=granularity,
        )
        for candidate in candidates
    ]
    return {
        "schema_version": 1,
        "purpose": "title-specific display-geometry review",
        "authority": "diagnostic-only until explicitly promoted",
        "framebuffer_geometry": [width, height],
        "validated_materializer_capacity_margin_pixels": capacity_margin,
        "materializer_granularity_pixels": granularity,
        "captures": captures,
        "candidates": rows,
    }


def _bmp_data_uri(path: Path) -> str:
    return "data:image/bmp;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def render_html(report: dict[str, Any]) -> str:
    capture_by_tag = {c["tag"]: c for c in report["captures"]}
    cards = []
    for candidate in report["candidates"]:
        par = parse_ratio(candidate["pixel_aspect"])
        sx = float(par)
        crop_top = candidate["crop_top"]
        crop_bottom = candidate["crop_bottom"]
        derived = candidate["derived_16x9"]
        margin = derived["materializer_margin_pixels"]
        capacity = derived.get("capacity_sufficient")
        for tag, capture in capture_by_tag.items():
            uri = _bmp_data_uri(Path(capture["path"]))
            width = capture["width"]
            height = capture["height"]
            active_height = candidate["active_logical_height"]
            shown_width = width * sx
            crop_css = (
                f"clip-path:inset({crop_top}px 0 {crop_bottom}px 0);"
                if crop_top or crop_bottom else ""
            )
            cards.append(f"""
<article>
<h3>{html.escape(candidate['label'])} · {html.escape(tag)}</h3>
<div class="meta">PAR {html.escape(candidate['pixel_aspect'])} · active {width}×{active_height} ·
stock display aspect {candidate['stock_display_aspect']['decimal']:.6f} ·
16:9 strip margin +{margin} · capacity {'yes' if capacity else 'no'}</div>
<div class="stage" style="width:{shown_width:.3f}px;height:{height}px">
<img src="{uri}" alt="{html.escape(tag)}" style="width:{shown_width:.3f}px;height:{height}px;{crop_css}">
</div>
</article>""")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Uniracers display geometry review</title>
<style>
body{{font:14px/1.4 system-ui,sans-serif;margin:20px;background:#111;color:#eee}}
.notice{{max-width:1000px;padding:12px;border:1px solid #555;background:#1b1b1b}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:18px;margin-top:18px}}
article{{border:1px solid #333;padding:12px;background:#181818;overflow:auto}}
h3{{margin:0 0 6px}} .meta{{color:#bbb;margin-bottom:8px}}
.stage{{position:relative;background:#000;overflow:hidden}}
.stage img{{display:block;image-rendering:pixelated;transform-origin:top left}}
</style></head><body>
<h1>Uniracers display geometry review</h1>
<div class="notice"><strong>Diagnostic only.</strong> These transforms are explicit candidates, not title-final constants.
Choose PAR/overscan only after comparison against retained Uniracers reference evidence. The 16:9 margin shown is
derived mechanically from each candidate and the validated materializer contract.</div>
<div class="grid">{''.join(cards)}</div>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=Path, required=True)
    ap.add_argument("--capture", action="append", type=Path, required=True)
    ap.add_argument("--capacity-margin", type=int, default=64)
    ap.add_argument("--granularity", type=int, default=8)
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--html-out", type=Path, required=True)
    args = ap.parse_args()

    config = json.loads(args.candidates.read_text(encoding="utf-8"))
    report = build_report(
        args.capture,
        config["candidates"],
        capacity_margin=args.capacity_margin,
        granularity=args.granularity,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.html_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.html_out.write_text(render_html(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
