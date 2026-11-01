#!/usr/bin/env python3
"""Audit authentic first-family racer P1/P2 colour identity by source pixels.

This is a 2D colour census, NOT original 3D material/lighting recovery.
Each distinct authentic 64x64 binary source silhouette gets one vote; source
repeats and identical editorial filenames do not multiply a colourway.
An explicitly documented high-chroma RGB rule identifies red/blue accents
without inventing UV/material/part labels or original camera geometry.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

try:
    from tools.art.build_racer_source_pixel_corpus import build, ROOT, STRIP
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from build_racer_source_pixel_corpus import build, ROOT, STRIP
    from racer_source_pixels import decode_rgba_png, alpha_metrics
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-FIRST-FAMILY-AUTHENTIC-2D-COLOURWAY/1"
CANONICAL_ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
FRAMES = tuple(range(1205, 1221))
PLAYERS = ("p1", "p2")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def hex_rgb(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{n:02x}" for n in rgb)


def classify_source_chroma(rgb: tuple[int, int, int]) -> str:
    """Explicit **heuristic** high-chroma accent indicator, not part labels.

    Source SNES sprites contain neutral grays and coloured pixels. This rule
    is an intentionally small, reproducible descriptor of the original RGB
    bytes; it does NOT identify a fork, face, wheel or model material.
    """
    r, g, b = rgb
    if r >= 64 and r > 2*g and r > 2*b:
        return "red"
    if b >= 64 and b > 2*g and b > 2*r:
        return "blue"
    return "other"


def analyse_source_rgba(rgba: bytes) -> dict:
    if not isinstance(rgba, bytes) or len(rgba) != 64*64*4:
        raise ValueError("source colour census requires exact original 64x64 RGBA")
    pixels = Counter()
    red = blue = other = opaque = 0
    for n in range(0, len(rgba), 4):
        r, g, b, a = rgba[n:n+4]
        if a not in (0, 255):
            raise ValueError("original pixel alpha is not binary; avoid accidental weighting")
        if not a:
            continue
        colour = (r, g, b)
        pixels[colour] += 1
        opaque += 1
        kind = classify_source_chroma(colour)
        red += kind == "red"
        blue += kind == "blue"
        other += kind == "other"
    if opaque == 0:
        raise ValueError("original source has no opaque racer pixels")
    if red + blue + other != opaque:
        raise ValueError("source colour occupancy partition changed")
    return {
        "source_opaque_pixels": opaque,
        "source_distinct_opaque_rgb_colours": len(pixels),
        "source_red_chroma_indicator_pixels": red,
        "source_blue_chroma_indicator_pixels": blue,
        "source_other_rgb_indicator_pixels": other,
        "source_red_chroma_fraction": round(red / opaque, 8),
        "source_blue_chroma_fraction": round(blue / opaque, 8),
        "source_opaque_rgb_histogram": [
            {"rgb_hex": hex_rgb(rgb), "pixel_count": count}
            for rgb, count in sorted(pixels.items(), key=lambda item: item[0])
        ],
    }


def aggregate_source_colourways(rows: list[dict], *,
                                source_rom_sha256: str,
                                source_registry_sha256: str) -> dict:
    """Pure, independently provenance-checked first-family colourway reducer.

    Every player/frame must occur once. A given exact original binary
    silhouette may have multiple original RGB variants; each variant is
    retained, and the silhouette still counts only ONCE in overall sums.
    """
    if (source_rom_sha256 != CANONICAL_ROM_SHA or
            not isinstance(source_registry_sha256, str) or
            len(source_registry_sha256) != 64 or
            any(c not in "0123456789abcdef" for c in source_registry_sha256)):
        raise ValueError("original ROM or registered source corpus identity invalid")
    if len(rows) != 32:
        raise ValueError("original first-family colour census requires 32 frame observations")
    by_mask = {}
    frames_seen = set()
    per_player = defaultdict(set)
    for row in rows:
        key = (row.get("player"), row.get("guest_frame"))
        if (key[0] not in PLAYERS or type(key[1]) is not int or
                key[1] not in FRAMES or key in frames_seen):
            raise ValueError("duplicate, out-of-range or invalid original racer frame")
        frames_seen.add(key)
        mask_sha, rgba_sha, png_sha = (
            row.get("source_binary_mask_sha256"),
            row.get("source_rgba_sha256"),
            row.get("source_png_sha256"),
        )
        if any(not isinstance(v, str) or len(v) != 64 or
               any(c not in "0123456789abcdef" for c in v)
               for v in (mask_sha, rgba_sha, png_sha)):
            raise ValueError("original per-frame pixel provenance SHA is invalid")
        if (not isinstance(row.get("representation_id"), str) or
                not row["representation_id"]):
            raise ValueError("original source representation identity is absent")
        rgba = row.get("source_decoded_rgba")
        if not isinstance(rgba, bytes) or digest(rgba) != rgba_sha:
            raise ValueError("original source decoded RGBA digest mismatch")
        alpha = bytes(int(x > 0) for x in rgba[3::4])
        if digest(alpha) != mask_sha:
            raise ValueError("original source binary-mask digest mismatch")
        stats = analyse_source_rgba(rgba)
        group = by_mask.setdefault((row["player"], mask_sha), {
            "player": row["player"],
            "source_binary_mask_sha256": mask_sha,
            "original_frame_references": [],
            "rgba_variants": {},
        })
        group["original_frame_references"].append({
            "guest_frame": row["guest_frame"],
            "representation_id": row["representation_id"],
            "source_png_sha256": png_sha,
        })
        variant = group["rgba_variants"].setdefault(rgba_sha, {
            "source_rgba_sha256": rgba_sha,
            "source_frame_count": 0,
            "source_color_stats": stats,
        })
        variant["source_frame_count"] += 1
        if variant["source_color_stats"] != stats:
            raise ValueError("identical source RGBA hash gave conflicting pixel statistics")
        per_player[row["player"]].add(mask_sha)
    if frames_seen != {(p, f) for p in PLAYERS for f in FRAMES}:
        raise ValueError("incomplete original P1/P2 temporal colour set")
    if len(by_mask) != 10 or len(per_player["p1"]) != 6 or len(per_player["p2"]) != 4:
        raise ValueError("original 10 source silhouettes / P1 six / P2 four changed")
    # Weight each distinct source silhouette once, and within it each
    # original colour-variant once. Frame-holds never become extra weights.
    summaries = {}
    for player in PLAYERS:
        groups = [group for (p, _), group in by_mask.items() if p == player]
        totals = {"red": 0.0, "blue": 0.0, "opaque": 0.0}
        signatures = []
        for group in groups:
            variants = list(group["rgba_variants"].values())
            n = len(variants)
            totals["red"] += sum(x["source_color_stats"]["source_red_chroma_indicator_pixels"]
                                 for x in variants) / n
            totals["blue"] += sum(x["source_color_stats"]["source_blue_chroma_indicator_pixels"]
                                  for x in variants) / n
            totals["opaque"] += sum(x["source_color_stats"]["source_opaque_pixels"]
                                    for x in variants) / n
            signatures.append({
                "source_binary_mask_sha256": group["source_binary_mask_sha256"],
                "original_source_frame_references": sorted(
                    group["original_frame_references"],
                    key=lambda x: x["guest_frame"]),
                "distinct_original_rgba_colour_variants": n,
                "original_rgba_variants": sorted(variants, key=lambda x: x["source_rgba_sha256"]),
            })
        summaries[player] = {
            "distinct_original_binary_silhouette_weight": len(groups),
            "mean_source_opaque_pixels_per_distinct_shape": round(totals["opaque"] / len(groups), 8),
            "mean_red_chroma_indicator_pixels_per_shape": round(totals["red"] / len(groups), 8),
            "mean_blue_chroma_indicator_pixels_per_shape": round(totals["blue"] / len(groups), 8),
            "mean_source_red_chroma_fraction_of_opaque_pixels": round(
                sum(sum(v["source_color_stats"]["source_red_chroma_fraction"]
                        for v in g["rgba_variants"].values()) / len(g["rgba_variants"])
                    for g in groups) / len(groups), 8),
            "mean_source_blue_chroma_fraction_of_opaque_pixels": round(
                sum(sum(v["source_color_stats"]["source_blue_chroma_fraction"]
                        for v in g["rgba_variants"].values()) / len(g["rgba_variants"])
                    for g in groups) / len(groups), 8),
            "source_shape_groups": sorted(signatures, key=lambda x: x["source_binary_mask_sha256"]),
        }
    return {
        "schema": SCHEMA,
        "source_rom_sha256": source_rom_sha256,
        "source_registry_sha256": source_registry_sha256,
        "original_64x64_observation_count": 32,
        "distinct_2d_binary_source_silhouettes": len(by_mask),
        "source_weighting": "one vote per distinct original binary silhouette, RGBA colour variants equal within same silhouette",
        "source_accents_are_heuristic": True,
        "source_red_chroma_rule": "R>=64 and R>2*G and R>2*B",
        "source_blue_chroma_rule": "B>=64 and B>2*G and B>2*R",
        "source_colour_is_an_authentic_3d_material_label": False,
        "1994_3d_camera_or_lighting_recovered": False,
        "original_sprite_to_2026_model_pose_mapping_verified": False,
        "owner_character_likeness_approved": False,
        "shipping_art_approved": False,
        "original_racer_source_colourways": summaries,
    }


def audit() -> dict:
    corpus = build()
    if (corpus.get("frame_observation_count") != 32 or
            corpus.get("historical_manifest_declared_rom_sha256") != CANONICAL_ROM_SHA or
            corpus.get("decoded_png_rgba_sha_verified_against_review_manifest") is not True):
        raise ValueError("original retained ROM-composed source provenance missing")
    rows = []
    cache = {}
    for obs in corpus["observations"]:
        path = (ROOT / obs["source_image"]).resolve()
        if not path.is_relative_to(STRIP.resolve()) or not path.is_file():
            raise ValueError("original source pixel file escaped retained authenticated strip")
        if path not in cache:
            cache[path] = decode_rgba_png(path)
        w, h, rgba, file_sha = cache[path]
        metrics = alpha_metrics(rgba, w, h)
        if ((w, h) != (64, 64) or file_sha != obs["png_file_sha256"] or
                metrics["source_rgba_sha256"] != obs["source_rgba_sha256"] or
                metrics["binary_mask_sha256"] != obs["binary_mask_sha256"]):
            raise ValueError("original source raster changed from independent hash corpus")
        rows.append({
            "player": obs["player"],
            "guest_frame": obs["guest_frame"],
            "representation_id": obs["representation_id"],
            "source_png_sha256": file_sha,
            "source_rgba_sha256": metrics["source_rgba_sha256"],
            "source_binary_mask_sha256": metrics["binary_mask_sha256"],
            "source_decoded_rgba": rgba,
        })
    report = aggregate_source_colourways(
        rows,
        source_rom_sha256=corpus["historical_manifest_declared_rom_sha256"],
        source_registry_sha256=corpus["source_registry_current_sha256"],
    )
    report["retained_source_manifest_sha256_by_player"] = corpus["showcase_manifest_sha256"]
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, help="immutable JSON receipt; stdout by default")
    args = ap.parse_args()
    rendered = json.dumps(audit(), indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
