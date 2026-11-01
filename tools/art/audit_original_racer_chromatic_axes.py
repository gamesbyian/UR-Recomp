#!/usr/bin/env python3
"""Original racer chromatic body-axis study from a SHA-bound hosted ROM corpus.

Measure source P1 red / P2 blue pixel directions without assuming these pixels
are authenticated original 3D fork geometry, a recovered 1994 camera, or a
sprite-to-2026-GLB pose map. Original masks and PNG bytes are authenticated.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile
from zipfile import ZipFile

try:
    from tools.art.freeze_racer_source_family_splits import (
        CANONICAL_ROM_SHA, OUTPUT_SCHEMA,
    )
    from tools.art.racer_source_pixels import decode_rgba_png
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from freeze_racer_source_family_splits import CANONICAL_ROM_SHA, OUTPUT_SCHEMA
    from racer_source_pixels import decode_rgba_png
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-AUTHENTIC-CHROMATIC-BODY-AXES/1"
EVIDENCE_SCHEMA = "UR-ART4K-REAL-HOSTED-CHROMATIC-AXIS-EVIDENCE/1"
EXPECTED_SOURCE = (Path(__file__).resolve().parents[2] /
                   "analysis/data/racer-art4k-hosted-chromatic-axes-20261101.json")
CORPUS_SCHEMA = "UR-RACER-ROM-COMPOSED-SOURCE-CORPUS/1"
PNG = re.compile(r"stock/source-[0-9a-f]{64}\.png\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


def pixel_masks(rgba: bytes, player: str):
    """Exact original RGBA and a deliberately *descriptive* chroma indicator."""
    if player not in ("p1", "p2") or len(rgba) != 64 * 64 * 4:
        raise ValueError("unexpected original player or 64x64 source shape")
    alpha = bytearray(4096)
    chroma = bytearray(4096)
    coordinates = []
    for i in range(4096):
        r, g, b, a = rgba[4*i:4*i+4]
        if a not in (0, 255):
            raise ValueError("original source raster has nonbinary alpha")
        if not a:
            continue
        alpha[i] = 1
        selected = (r >= 64 and r > 2*g and r > 2*b) if player == "p1" else (
            b >= 64 and b > 2*g and b > 2*r)
        if selected:
            chroma[i] = 1
            coordinates.append((i % 64, i // 64))
    if not any(alpha) or len(coordinates) < 3:
        raise ValueError("source lacks enough authentic chromatic pixels")
    return bytes(alpha), bytes(chroma), coordinates


def principal_axis(points) -> dict:
    """PCA chromatic-region angle from screen-down Y; not a physical 3D lean."""
    pts = list(points)
    if len(pts) < 3 or any(len(p) != 2 or
                           any(type(v) not in (int, float) or not math.isfinite(v)
                               for v in p) for p in pts):
        raise ValueError("invalid original chromatic coordinates")
    n = len(pts)
    cx = sum(x for x, _ in pts) / n
    cy = sum(y for _, y in pts) / n
    xx = sum((x-cx)**2 for x, _ in pts) / n
    yy = sum((y-cy)**2 for _, y in pts) / n
    xy = sum((x-cx)*(y-cy) for x, y in pts) / n
    trace = xx + yy
    if trace <= 1e-12:
        raise ValueError("degenerate chromatic source axis")
    major = (trace + math.hypot(xx-yy, 2*xy)) / 2
    angle = math.degrees(0.5 * math.atan2(2*xy, yy-xx))
    return {
        "chroma_pixel_count": n,
        "centroid_source_xy": [round(cx, 6), round(cy, 6)],
        "screen_axis_angle_from_down_y_degrees": round(angle, 6),
        "source_chroma_pca_major_variance_fraction": round(major / trace, 6),
    }


def row_envelope_sha(alpha: bytes) -> str:
    if len(alpha) != 4096 or any(v not in (0, 1) for v in alpha):
        raise ValueError("invalid original binary silhouette")
    envelope = bytearray(4096)
    for y in range(64):
        xs = [x for x in range(64) if alpha[y*64 + x]]
        if xs:
            for x in range(min(xs), max(xs) + 1):
                envelope[y*64 + x] = 1
    return hashlib.sha256(envelope).hexdigest()


def temporal_source_axes(observations, rows) -> dict:
    """Reconstruct exact guest-frame chromatic records and repeated holds.

    The registered source timeline is an original 2D representation sequence,
    not proven continuous 3D source animation, pedal phase or rig bone motion.
    """
    if not isinstance(observations, list) or not observations:
        raise ValueError("source temporal observations missing")
    by_id = {row["source_representation_id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate source representation in colour axis census")
    sequences = defaultdict(list)
    seen = set()
    for sample in observations:
        if not isinstance(sample, dict):
            raise ValueError("invalid source frame record")
        name, frame, players = (sample.get("window"), sample.get("guest_frame"),
                                sample.get("representations"))
        if (not isinstance(name, str) or not name or type(frame) is not int or
                not isinstance(players, dict) or not players or
                any(player not in ("p1", "p2") or rid not in by_id or
                    by_id[rid]["player"] != player
                    for player, rid in players.items())):
            raise ValueError("unrecognized original registered frame")
        if (name, frame) in seen:
            raise ValueError("duplicate original guest frame in a source window")
        seen.add((name, frame))
        sequences[name].append({
            "guest_frame": frame,
            "source_player_axes": {
                player: {
                    "source_representation_id": rid,
                    "source_binary_mask_sha256":
                        by_id[rid]["source_binary_mask_sha256"],
                    "source_chromatic_mask_sha256":
                        by_id[rid]["source_chromatic_mask_sha256"],
                    "screen_axis_angle_from_down_y_degrees":
                        by_id[rid]["screen_axis_angle_from_down_y_degrees"],
                } for player, rid in sorted(players.items())
            },
        })
    result = {}
    for name, timeline in sorted(sequences.items()):
        if any(timeline[i]["guest_frame"] >= timeline[i+1]["guest_frame"]
               for i in range(len(timeline)-1)):
            raise ValueError("source window is not strictly chronological")
        holds = {}
        for player in ("p1", "p2"):
            segments = []
            for row in timeline:
                p = row["source_player_axes"].get(player)
                if p is None:
                    continue
                identity = p["source_chromatic_mask_sha256"]
                if segments and segments[-1]["source_chromatic_mask_sha256"] == identity:
                    segments[-1]["last_guest_frame"] = row["guest_frame"]
                    segments[-1]["observed_frame_count"] += 1
                else:
                    segments.append({
                        "source_chromatic_mask_sha256": identity,
                        "first_guest_frame": row["guest_frame"],
                        "last_guest_frame": row["guest_frame"],
                        "observed_frame_count": 1,
                        "screen_axis_angle_from_down_y_degrees":
                            p["screen_axis_angle_from_down_y_degrees"],
                    })
            if segments:
                holds[player] = segments
        result[name] = {
            "source_frame_observation_count": len(timeline),
            "source_visible_chromatic_holds": holds,
            "observations": timeline,
        }
    return result


def verify_pinned_source_bytes(source: dict, archive_sha: str,
                               corpus_sha: str, frozen_sha: str) -> None:
    """Require independently published exact source evidence, not self-declared SHA."""
    if not isinstance(source, dict) or source.get("schema") != EVIDENCE_SCHEMA:
        raise ValueError("missing trusted original source evidence contract")
    for measured, key in (
            (archive_sha, "source_artifact_zip_sha256"),
            (corpus_sha, "original_source_manifest_sha256"),
            (frozen_sha, "frozen_source_split_sha256")):
        if source.get(key) != measured:
            raise ValueError("original source bytes differ from pinned GitHub evidence")


def audit(artifact: Path, evidence_path: Path = EXPECTED_SOURCE) -> dict:
    raw_zip = artifact.read_bytes()
    reference = json.loads(evidence_path.read_text(encoding="utf-8"))
    with ZipFile(artifact) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(
                name.startswith("/") or ".." in Path(name).parts or
                "\\" in name for name in names):
            raise ValueError("duplicate or unsafe original source ZIP member")
        corpus_bytes = archive.read("source-corpus.json")
        frozen_bytes = archive.read("frozen-first-family-holdout.json")
        corpus, frozen = json.loads(corpus_bytes), json.loads(frozen_bytes)
        verify_pinned_source_bytes(
            reference, hashlib.sha256(raw_zip).hexdigest(),
            hashlib.sha256(corpus_bytes).hexdigest(),
            hashlib.sha256(frozen_bytes).hexdigest())
        if (corpus.get("schema") != CORPUS_SCHEMA or
                corpus.get("source_rom_sha256") != CANONICAL_ROM_SHA or
                corpus.get("source_rom_verified_and_used_for_composition") is not True or
                frozen.get("schema") != OUTPUT_SCHEMA or
                frozen.get("source_rom_sha256") != CANONICAL_ROM_SHA or
                frozen.get("corpus_manifest_sha256") != hashlib.sha256(corpus_bytes).hexdigest() or
                frozen.get("no_original_binary_silhouette_across_roles") is not True or
                frozen.get("withheld_candidate_is_an_independent_3d_camera") is not False or
                frozen.get("owner_likeness_approved") is not False or
                frozen.get("shipping_art_approved") is not False):
            raise ValueError("original ROM/source split provenance mismatch")
        roles = {}
        for component in frozen.get("connected_window_components", []):
            if component.get("role") not in ("fit", "withheld_candidate"):
                raise ValueError("unfrozen or alien source group")
            for mask in component.get("source_binary_mask_shas", []):
                if not isinstance(mask, str) or not SHA.fullmatch(mask) or mask in roles:
                    raise ValueError("duplicate or invalid original source mask group")
                roles[mask] = component["role"]
        represented = corpus.get("source_representations")
        if not isinstance(represented, dict) or len(represented) < 35:
            raise ValueError("expected authenticated original representations")
        rows = []
        verified_pngs = set()
        with tempfile.TemporaryDirectory(prefix="ur-art4k-source-axes-") as directory:
            root = Path(directory)
            for rid, entry in sorted(represented.items()):
                if not isinstance(entry, dict) or not isinstance(rid, str):
                    raise ValueError("invalid source representation record")
                name = entry.get("local_file")
                if not isinstance(name, str) or not PNG.fullmatch(name):
                    raise ValueError("untrusted source PNG path in original corpus")
                actual = archive.read(name)
                if (not isinstance(entry.get("local_png_sha256"), str) or
                        hashlib.sha256(actual).hexdigest() != entry["local_png_sha256"]):
                    raise ValueError("actual source PNG bytes mismatch")
                temp = root / Path(name).name
                temp.write_bytes(actual)
                width, height, rgba, read_sha = decode_rgba_png(temp)
                if (width, height) != (64, 64) or read_sha != entry["local_png_sha256"] or (
                        hashlib.sha256(rgba).hexdigest() != entry.get("source_rgba_sha256")):
                    raise ValueError("actual decoded original raster mismatch")
                alpha, chroma, coordinates = pixel_masks(rgba, entry.get("player"))
                shape_sha = hashlib.sha256(alpha).hexdigest()
                if shape_sha != entry.get("source_binary_mask_sha256") or shape_sha not in roles:
                    raise ValueError("unregistered original binary shape")
                verified_pngs.add(name)
                rows.append({
                    "source_representation_id": rid,
                    "player": entry["player"],
                    "role": roles[shape_sha],
                    "source_binary_mask_sha256": shape_sha,
                    "source_rgba_sha256": entry["source_rgba_sha256"],
                    "source_chromatic_mask_sha256": hashlib.sha256(chroma).hexdigest(),
                    "source_external_row_envelope_sha256": row_envelope_sha(alpha),
                    **principal_axis(coordinates),
                })
        if (len(roles) != corpus.get("unique_binary_silhouettes") or
                len(verified_pngs) != corpus.get("unique_rgba_images") or
                set(x["source_binary_mask_sha256"] for x in rows) != set(roles)):
            raise ValueError("incomplete or altered original source silhouette census")

    by_shape = defaultdict(list)
    chroma_roles = defaultdict(set)
    for row in rows:
        by_shape[row["source_binary_mask_sha256"]].append(row)
        chroma_roles[row["source_chromatic_mask_sha256"]].add(row["role"])
    shape_rows = []
    for mask, variants in sorted(by_shape.items()):
        # Same source shape may have multiple actual chromatic colour variants;
        # repeated temporal holds or aliases must not multiply its weight.
        per_variant = {v["source_chromatic_mask_sha256"]: v
                       for v in variants}
        angles = [v["screen_axis_angle_from_down_y_degrees"]
                  for v in per_variant.values()]
        shape_rows.append({
            "source_binary_mask_sha256": mask,
            "role": roles[mask],
            "players": sorted({v["player"] for v in variants}),
            "source_external_row_envelope_sha256":
                variants[0]["source_external_row_envelope_sha256"],
            "original_chromatic_shape_variants": len(per_variant),
            "mean_chromatic_source_screen_axis_degrees":
                round(sum(angles)/len(angles), 6),
        })
    summary = {}
    for role in ("fit", "withheld_candidate"):
        sub = [r for r in shape_rows if r["role"] == role]
        summary[role] = {
            "independent_original_binary_masks": len(sub),
            "independent_external_row_envelopes":
                len({r["source_external_row_envelope_sha256"] for r in sub}),
            "per_player": {},
        }
        for player in ("p1", "p2"):
            relevant = [r["mean_chromatic_source_screen_axis_degrees"]
                        for r in sub if player in r["players"]]
            if relevant:
                summary[role]["per_player"][player] = {
                    "shape_count": len(relevant),
                    "equal_source_binary_shape_mean_axis_degrees":
                        round(sum(relevant)/len(relevant), 6),
                    "minimum_axis_degrees": min(relevant),
                    "maximum_axis_degrees": max(relevant),
                }
    return {
        "schema": SCHEMA,
        "source_artifact_zip_sha256": hashlib.sha256(raw_zip).hexdigest(),
        "source_corpus_manifest_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "frozen_source_split_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
        "original_canonical_rom_sha256": CANONICAL_ROM_SHA,
        "actual_verified_source_png_count": len(verified_pngs),
        "source_original_representation_count": len(rows),
        "source_chromatic_indicator":
            "P1 R>=64,R>2G,R>2B; P2 B>=64,B>2G,B>2R; no 3D semantic-part attribution",
        "unique_source_chromatic_masks": len(chroma_roles),
        "exact_chromatic_source_masks_crossing_fit_and_withheld": sorted(
            sha for sha, roleset in chroma_roles.items() if len(roleset) > 1),
        "summary": summary,
        "source_binary_shape_rows": shape_rows,
        "original_guest_frame_chromatic_trajectories":
            temporal_source_axes(corpus.get("source_temporal_frame_observations"), rows),
        "original_screen_axis_is_source_3d_lean_angle": False,
        "original_1994_3d_camera_identified": False,
        "2026_glb_sprite_pose_correspondence_verified": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_artifact_zip", type=Path)
    parser.add_argument("--evidence", type=Path, default=EXPECTED_SOURCE,
                        help="committed exact original ZIP/corpus/split source SHA contract")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    content = json.dumps(audit(args.source_artifact_zip, args.evidence),
                         sort_keys=True, indent=2) + "\n"
    if args.out:
        publish_text_once(args.out, content)
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
