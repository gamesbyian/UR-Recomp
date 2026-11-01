#!/usr/bin/env python3
"""Measure registered 64px original vs 1x/4x candidate racer silhouette.

This deliberately preserves every source canvas coordinate and never chooses
a per-pose translation/zoom. It reports geometry metrics, not art approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from math import hypot
from pathlib import Path

try:
    from tools.art.build_racer_source_pixel_corpus import build as original_corpus, ROOT, STRIP
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
except ModuleNotFoundError:
    from build_racer_source_pixel_corpus import build as original_corpus, ROOT, STRIP
    from racer_source_pixels import decode_rgba_png, alpha_metrics


def mask_from_rgba(rgba: bytes, width: int, height: int, scale: int = 1) -> tuple[int, ...]:
    if scale not in (1, 4) or (width, height) != (64 * scale, 64 * scale):
        raise ValueError("candidate must have a registered 64x64 or 4x 256x256 canvas")
    if len(rgba) != width * height * 4:
        raise ValueError("candidate raster length is inconsistent with dimensions")
    offset = scale // 2 if scale == 4 else 0
    return tuple(
        1 if rgba[((y*scale+offset)*width + x*scale+offset)*4+3] else 0
        for y in range(64) for x in range(64)
    )


def _occupied(mask):
    if len(mask) != 4096:
        raise ValueError("mask must be 64x64")
    result = {(i % 64, i // 64) for i, pixel in enumerate(mask) if pixel}
    if not result:
        raise ValueError("source/candidate silhouette is empty")
    return result


def _bbox(points):
    return [min(x for x, _ in points), min(y for _, y in points),
            max(x for x, _ in points), max(y for _, y in points)]


def _lowest_contact(points):
    """Projected lowest occupied alpha span, not proven wheel-ground contact."""
    y = max(y for _, y in points)
    row = [x for x, yy in points if yy == y]
    return (min(row)+max(row), 2*y)


def _boundary(points):
    return {(x, y) for x, y in points if any(
        (x+dx, y+dy) not in points
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )}


def score(reference_mask, candidate_mask):
    ref, candidate = _occupied(reference_mask), _occupied(candidate_mask)
    common, union = ref & candidate, ref | candidate
    ref_edge, candidate_edge = _boundary(ref), _boundary(candidate)

    def directed(a, b):
        return sum(min(hypot((x-u)*7/6, y-v) for u, v in b)
                   for x, y in a) / len(a)

    contact_a, contact_b = _lowest_contact(ref), _lowest_contact(candidate)
    return {
        "logical_canvas": [64, 64],
        "snes_pixel_aspect": "7:6",
        "mask_iou": round(len(common)/len(union), 8),
        "mask_intersection": len(common),
        "mask_union": len(union),
        "mask_xor_pixels": len(ref ^ candidate),
        "reference_opaque": len(ref),
        "candidate_opaque": len(candidate),
        "reference_bbox_xyxy": _bbox(ref),
        "candidate_bbox_xyxy": _bbox(candidate),
        "reference_lowest_alpha_x2_y2": list(contact_a),
        "candidate_lowest_alpha_x2_y2": list(contact_b),
        "lowest_alpha_delta_x2_y2": [b-a for a, b in zip(contact_a, contact_b)],
        "boundary_chamfer_mean_physical_px": round((
            directed(ref_edge, candidate_edge) +
            directed(candidate_edge, ref_edge)) / 2, 8),
        "auto_registration_performed": False,
        "original_3d_rig_verified": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def score_retained_original(player: str, guest_frame: int, candidate_png: Path,
                            expected_candidate_file_sha: str, scale: int) -> dict:
    if player not in ("p1", "p2") or guest_frame not in range(1205, 1221):
        raise ValueError("unsupported source first-family player/frame")
    if (len(expected_candidate_file_sha) != 64 or
            any(c not in "0123456789abcdef" for c in expected_candidate_file_sha)):
        raise ValueError("candidate image requires exact lowercase SHA256")
    corpus = original_corpus()  # Decodes/verifies every authentic retained source PNG.
    observation = next(
        x for x in corpus["observations"]
        if x["player"] == player and x["guest_frame"] == guest_frame
    )
    source_path = ROOT / observation["source_image"]
    w, h, source_pixels, source_file_sha = decode_rgba_png(source_path)
    source_metrics = alpha_metrics(source_pixels, w, h)
    if (source_file_sha != observation["png_file_sha256"] or
            source_metrics["source_rgba_sha256"] != observation["source_rgba_sha256"]):
        raise ValueError("retained original source changed since corpus audit")
    cw, ch, candidate, candidate_file_sha = decode_rgba_png(candidate_png)
    if candidate_file_sha != expected_candidate_file_sha:
        raise ValueError("candidate PNG SHA256 does not match submitted immutable image")
    source_mask = mask_from_rgba(source_pixels, w, h, 1)
    candidate_mask = mask_from_rgba(candidate, cw, ch, scale)
    return {
        "schema": "UR-RACER-REGISTERED-SILHOUETTE-SCORE/1",
        "player": player, "guest_frame": guest_frame,
        "source_representation_id": observation["representation_id"],
        "source_png_sha256": source_file_sha,
        "source_rgba_sha256": observation["source_rgba_sha256"],
        "candidate_png_sha256": candidate_file_sha,
        "candidate_render_density": scale,
        "candidate_is_identical_original_png": candidate_file_sha == source_file_sha,
        "candidate_mesh_identity_verified": False,
        "source_rom_reextracted": False,
        **score(source_mask, candidate_mask),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--player", choices=("p1", "p2"), required=True)
    ap.add_argument("--frame", type=int, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--candidate-sha256", required=True)
    ap.add_argument("--density", type=int, choices=(1, 4), required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = score_retained_original(
        args.player, args.frame, args.candidate, args.candidate_sha256, args.density
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
