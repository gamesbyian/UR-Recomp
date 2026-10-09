#!/usr/bin/env python3
"""QA-08: locate possible foreground occlusion loss from same-frame PPU layers.

The pinned PPU exports isolated stock OBJ colours even when that OBJ is behind
an opaque BG pixel. Compare its RGBA layer to a separately captured exact
Original frame, then ask whether HD painted over a suspect pixel. This is an
adversarial candidate finder, not a proof of why colours differed: colour math,
other stock OBJ, and palette effects can also produce differences.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_racer_hd_pixel_confinement import (
    allowed_logical_mask, live_placements, parse_ppm,
)

WIDTH, HEIGHT = 256, 224
PAM_HEADER = (
    b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
    b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
)


def parse_obj_pam(data: bytes) -> bytes:
    if not data.startswith(PAM_HEADER):
        raise ValueError("unsupported/malformed isolated stock OBJ PAM header")
    layer = data[len(PAM_HEADER):]
    if len(layer) != WIDTH * HEIGHT * 4:
        raise ValueError("isolated stock OBJ RGBA byte count mismatch")
    return layer


def analyze(original: bytes, original_control: bytes, hd: bytes,
            isolated: bytes, native_log: str, frame: int,
            *, obj_only_ppm: bytes | None = None) -> dict:
    if original != original_control:
        raise ValueError("independent Original references differ")
    sw, sh, stock = parse_ppm(original)
    hw, hh, remastered = parse_ppm(hd)
    if (sw, sh) != (WIDTH, HEIGHT):
        raise ValueError("Original frame must be complete 256x224")
    if hw % sw or hh % sh or hw // sw != hh // sh:
        raise ValueError("HD frame has invalid anisotropic or noninteger scale")
    scale = hw // sw
    if scale not in range(1, 5):
        raise ValueError("unsupported replacement raster density")
    backdrop_rgb = None
    backdrop_sample_count = None
    if obj_only_ppm is None:
        obj_rgba = parse_obj_pam(isolated)
        layer_origin = "isolated-ARGB-layer-PAM"
    else:
        ow, oh, layer_rgb = parse_ppm(obj_only_ppm)
        if (ow, oh) != (WIDTH, HEIGHT):
            raise ValueError("OBJ-only PPM must be exactly 256x224")
        # OBJ-only does not force the backdrop to black: native uses red.
        # PPM lacks alpha, so infer a uniformly dominant backdrop RGB,
        # excluding all matching pixels. This intentionally excludes
        # indistinguishable real OBJ pixels too: a conservative lower bound.
        colors = Counter(
            layer_rgb[i:i + 3] for i in range(0, len(layer_rgb), 3)
        )
        majority, backdrop_sample_count = colors.most_common(1)[0]
        if backdrop_sample_count < (WIDTH * HEIGHT * 3) // 4:
            raise ValueError(
                "OBJ-only backdrop is not sufficiently uniform to "
                "disambiguate from sprite pixels"
            )
        backdrop_rgb = list(majority)
        obj_rgba = bytearray(WIDTH * HEIGHT * 4)
        for i in range(WIDTH * HEIGHT):
            rgb = layer_rgb[i * 3:i * 3 + 3]
            obj_rgba[i * 4:i * 4 + 3] = rgb
            obj_rgba[i * 4 + 3] = 255 if rgb != majority else 0
        layer_origin = "independent-original-OBJ-only-PPM-backdrop-excluded-lower-bound"
    mask = allowed_logical_mask(live_placements(native_log, frame))
    visible_stock_obj = 0
    ambiguous_obj_pixels = 0
    hd_overpaint_candidates = 0
    hd_changed_direct_stock_obj_pixels = 0
    sample_ambiguous = []
    sample_overpaint = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            i = y * WIDTH + x
            if not mask[i]:
                continue
            q = i * 4
            if obj_rgba[q + 3] == 0:
                continue
            rgb = obj_rgba[q:q + 3]
            stock_pixel = stock[i * 3:i * 3 + 3]
            # Any density subpixel differing from the Original reference
            # signals HD replaced/modified the source logical pixel.
            changed = any(
                remastered[((y * scale + sy) * hw + x * scale + sx) * 3:
                           ((y * scale + sy) * hw + x * scale + sx) * 3 + 3]
                != stock_pixel
                for sy in range(scale) for sx in range(scale)
            )
            if stock_pixel == rgb:
                visible_stock_obj += 1
                if changed: hd_changed_direct_stock_obj_pixels += 1
                continue
            ambiguous_obj_pixels += 1
            if len(sample_ambiguous) < 12:
                sample_ambiguous.append([x, y])
            if changed:
                hd_overpaint_candidates += 1
                if len(sample_overpaint) < 12:
                    sample_overpaint.append([x, y])

    if visible_stock_obj + ambiguous_obj_pixels == 0:
        raise ValueError("isolated OBJ surface has no opaque racer pixels")
    return {
        "schema_version": 1,
        "source_layer_classification": layer_origin,
        "excluded_backdrop_rgb": backdrop_rgb,
        "backdrop_pixel_count": backdrop_sample_count,
        "frame": frame,
        "density": scale,
        "native_split_obj_opaque_pixels": visible_stock_obj + ambiguous_obj_pixels,
        "stock_obj_matches_original_rgb_pixels": visible_stock_obj,
        "stock_obj_differs_from_original_rgb_pixels": ambiguous_obj_pixels,
        "hd_modifies_obj_pixels_that_match_original": hd_changed_direct_stock_obj_pixels,
        "potential_foreground_occlusion_overpaint_pixels": hd_overpaint_candidates,
        "ambiguous_source_pixel_examples": sample_ambiguous,
        "overpaint_pixel_examples": sample_overpaint,
        "evidence_scope": (
            "diagnostic foreground/colour-math candidate search inside live "
            "racer OAM bounds; source-raster colour mismatch is not independently "
            "proven BG priority without a renderer layer/priority witness"
        ),
        "review_required": hd_overpaint_candidates > 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--original-control", type=Path, required=True)
    ap.add_argument("--hd", type=Path, required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--obj-layer", type=Path)
    group.add_argument("--obj-only-ppm", type=Path)
    ap.add_argument("--native-log", type=Path, required=True)
    ap.add_argument("--frame", type=int, required=True)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = analyze(
        args.original.read_bytes(),
        args.original_control.read_bytes(),
        args.hd.read_bytes(),
        args.obj_layer.read_bytes() if args.obj_layer else b"",
        args.native_log.read_text(encoding="utf-8", errors="replace"),
        args.frame,
        obj_only_ppm=args.obj_only_ppm.read_bytes() if args.obj_only_ppm else None,
    )
    result = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(result, encoding="utf-8")
    print(
        "UR_RACER_HD_FOREGROUND "
        f"frame={report['frame']} foreground_candidates="
        f"{report['potential_foreground_occlusion_overpaint_pixels']} "
        f"ambiguous={report['stock_obj_differs_from_original_rgb_pixels']} "
        f"needs_review={int(report['review_required'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
