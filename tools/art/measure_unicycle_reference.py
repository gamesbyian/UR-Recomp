#!/usr/bin/env python3
"""Measure *projected* unicycle character proportions from tagged local PNGs.

This is a ROM-free, image-reading-free landmark audit. Each human-marked point
is bound to an exact reference PNG hash and perspective description. Outputs
only dimensionless 2D observations, NEVER inferred 3D geometry or approval.
The local source reference remains out of the repository and output report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

try:
    from tools.art.validate_upscale_trials import (
        check_identity, ensure, TrialError,
    )
except ModuleNotFoundError:
    from validate_upscale_trials import check_identity, ensure, TrialError


SCHEMA = "UR-RACER-LIKENESS-LANDMARKS/1"
REPORT_SCHEMA = "UR-RACER-LIKENESS-PROJECTED-MEASURES/1"
SOURCE_KINDS = {
    "original-gameplay", "original-title", "official-packaging",
    "period-promotional", "artist-blockout",
}
VIEW_ANGLES = {"side", "three-quarter", "front", "unknown"}
PIXEL_ASPECT = {"square": 1.0, "snes_7_6": 7.0 / 6.0}
NEEDED = ("wheel_left", "wheel_right", "wheel_top", "wheel_bottom",
          "saddle_left", "saddle_right", "saddle_top", "saddle_bottom")
PAIRS = (("crown_left", "crown_right", "crown_width_over_wheel_diameter"),
         ("fork_left", "fork_right", "fork_spread_over_wheel_diameter"))
OPTIONAL = ("axle", "pedal_center", "crown_left", "crown_right",
            "fork_left", "fork_right")


def text_field(value, label: str) -> str:
    ensure(isinstance(value, str) and bool(value.strip()),
           f"{label} must be nonempty text")
    return value.strip()


def point(value, label: str, width: int, height: int) -> tuple[float, float]:
    ensure(isinstance(value, list) and len(value) == 2 and
           all(isinstance(v, (float, int)) and not isinstance(v, bool)
               for v in value) and
           all(v == v and abs(v) != float("inf") for v in value),
           f"{label} must have two finite numeric pixel coordinates")
    x, y = value
    ensure(0 <= x < width and 0 <= y < height,
           f"{label} is outside the actual source image")
    return float(x), float(y)


def measure_view(record: dict, base: Path) -> dict:
    ensure(isinstance(record, dict), "each reference view must be an object")
    ident = text_field(record.get("id"), "view id")
    source = record.get("source")
    ensure(isinstance(source, dict), f"{ident}: missing source provenance")
    kind = source.get("kind")
    ensure(kind in SOURCE_KINDS, f"{ident}: unknown source category")
    url = text_field(source.get("url"), f"{ident}: source URL")
    u = urlparse(url)
    ensure(u.scheme == "https" and bool(u.hostname) and
           u.username is None and u.password is None,
           f"{ident}: provenance source URL must be public HTTPS")
    for required in ("creator_or_credit", "region_or_version",
                     "capture_context", "rights_notes"):
        text_field(source.get(required), f"{ident}: {required}")
    image = record.get("image")
    img, (width, height, _) = check_identity(base, image, f"{ident}: image")
    view = record.get("view")
    ensure(isinstance(view, dict), f"{ident}: missing view description")
    angle = view.get("angle")
    ensure(angle in VIEW_ANGLES, f"{ident}: unknown view angle")
    pose = text_field(view.get("pose"), f"{ident}: pose")
    crop = text_field(view.get("crop_and_rescale_history"),
                      f"{ident}: crop/rescale history")
    annotator = text_field(record.get("annotator"), f"{ident}: annotator")
    aspect = view.get("pixel_aspect")
    ensure(aspect in PIXEL_ASPECT, f"{ident}: pixel aspect is not grounded")
    landmarks = record.get("landmarks")
    ensure(isinstance(landmarks, dict), f"{ident}: no landmarks")
    ensure(set(NEEDED).issubset(landmarks), f"{ident}: incomplete wheel/saddle bounds")
    ensure(set(landmarks).issubset(set(NEEDED) | set(OPTIONAL)),
           f"{ident}: unknown landmark name")
    pts = {name: point(value, f"{ident}: {name}", width, height)
           for name, value in landmarks.items()}
    for name in ("wheel", "saddle"):
        left, right = pts[f"{name}_left"], pts[f"{name}_right"]
        top, bottom = pts[f"{name}_top"], pts[f"{name}_bottom"]
        ensure(left[0] < right[0] and top[1] < bottom[1],
               f"{ident}: inverted {name} bounds")
    missing = record.get("unmeasurable", {})
    ensure(isinstance(missing, dict) and
           set(missing).issubset({"crown", "fork", "pedal", "axle"}),
           f"{ident}: unmeasurable must name known occluded features")
    for feature, keys in (("crown", ("crown_left", "crown_right")),
                          ("fork", ("fork_left", "fork_right")),
                          ("pedal", ("pedal_center",)),
                          ("axle", ("axle",))):
        present = [name in pts for name in keys]
        ensure(all(present) or not any(present),
               f"{ident}: partial {feature} landmark pair")
        ensure((feature in missing) != all(present),
               f"{ident}: mark {feature} or explain why it is unmeasurable")
        if feature in missing:
            text_field(missing[feature], f"{ident}: {feature} visibility reason")
    diameter = pts["wheel_bottom"][1] - pts["wheel_top"][1]
    factor = PIXEL_ASPECT[aspect]
    projected = {
        "wheel_width_over_wheel_height":
            round((pts["wheel_right"][0] - pts["wheel_left"][0]) * factor / diameter, 6),
        "saddle_width_over_wheel_diameter":
            round((pts["saddle_right"][0] - pts["saddle_left"][0]) * factor / diameter, 6),
        "saddle_height_over_wheel_diameter":
            round((pts["saddle_bottom"][1] - pts["saddle_top"][1]) / diameter, 6),
        "saddle_top_minus_wheel_top_over_wheel_diameter":
            round((pts["saddle_top"][1] - pts["wheel_top"][1]) / diameter, 6),
    }
    for l, r, name in PAIRS:
        projected[name] = (
            round((pts[r][0] - pts[l][0]) * factor / diameter, 6)
            if l in pts else None
        )
        if l in pts:
            ensure(pts[l][0] < pts[r][0], f"{ident}: inverted {name}")
    if "pedal_center" in pts and "axle" in pts:
        projected["pedal_horizontal_offset_over_wheel_diameter"] = round(
            (pts["pedal_center"][0] - pts["axle"][0]) * factor / diameter, 6)
        projected["pedal_vertical_offset_over_wheel_diameter"] = round(
            (pts["pedal_center"][1] - pts["axle"][1]) / diameter, 6)
    else:
        projected["pedal_horizontal_offset_over_wheel_diameter"] = None
        projected["pedal_vertical_offset_over_wheel_diameter"] = None
    return {
        "reference_id": ident,
        "image_sha256": image["sha256"],
        "image_dimensions": [width, height],
        "source_url": url,
        "source_kind": kind,
        "source_credit": source["creator_or_credit"],
        "region_or_version": source["region_or_version"],
        "capture_context": source["capture_context"],
        "rights_notes": source["rights_notes"],
        "view_angle": angle,
        "pose": pose,
        "pixel_aspect": aspect,
        "crop_and_rescale_history": crop,
        "annotator": annotator,
        "landmark_pixel_coordinates": {key: list(pts[key]) for key in sorted(pts)},
        "unmeasurable": missing,
        "projected_ratios": projected,
        "perspective_corrected_or_source_3d_model_proven": False,
        "human_likeness_approval": False,
    }


def measure(manifest: Path) -> dict:
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    ensure(isinstance(raw, dict) and raw.get("schema") == SCHEMA,
           "unknown likeness landmark schema")
    entries = raw.get("views")
    ensure(isinstance(entries, list) and bool(entries),
           "at least one tagged local reference view is required")
    results = [measure_view(entry, manifest.resolve().parent)
               for entry in entries]
    ids = [row["reference_id"] for row in results]
    ensure(len(set(ids)) == len(ids), "duplicate reference IDs")
    return {
        "schema": REPORT_SCHEMA,
        "view_count": len(results),
        "views": results,
        "three_dimensional_character_proportions_proven": False,
        "current_character_likeness_approved": False,
        "shipping_art_approved": False,
        "note": ("Projected, perspective-tagged measurements from user-supplied "
                 "unaltered-hash PNGs. Cross-view ratios are not comparable "
                 "until perspective and crop have been independently aligned. "
                 "No source pixels are embedded, no historical art approval "
                 "is changed, and no host asset is promoted."),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    try:
        report = measure(args.manifest)
    except (TrialError, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        p.exit(2, f"invalid character reference landmarks: {exc}\n")
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
