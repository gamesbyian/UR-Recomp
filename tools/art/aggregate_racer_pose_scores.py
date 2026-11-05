#!/usr/bin/env python3
"""Group authentic racer source-vs-GLB receipts by actual binary silhouettes.

Frame repetitions, same-pixel aliases and palette variants get ONE pose weight.
This is a first-family diagnostic; no source-independent 3D camera or withheld
source-family is certified. Model source must remain one exact shared SCAD.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

try:
    from tools.art.build_racer_source_pixel_corpus import build as original_corpus
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
    from tools.art.score_racer_candidate import score_retained_original
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from build_racer_source_pixel_corpus import build as original_corpus
    from racer_source_pixels import decode_rgba_png, alpha_metrics
    from score_racer_candidate import score_retained_original
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-MULTIPOSE-SCORE-SUITE/1"
REPORT_SCHEMA = "UR-RACER-MULTIPOSE-SCORE-REPORT/1"
PACKET_SCHEMA = "UR-RACER-SOURCE-RIG-EVIDENCE-PACKET/1"
ROLES = {"fit", "diagnostic"}
HEX = set("0123456789abcdef")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hex64(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in HEX for c in value)


def _safe_file(root: Path, name: str, suffix: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("unsafe manifest input path")
    path = Path(name)
    if path.is_absolute() or any(p in ("", ".", "..") for p in path.parts) or path.suffix != suffix:
        raise ValueError("unsafe manifest input path")
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()) or not result.is_file():
        raise ValueError("missing or escaping manifest source file")
    return result


def summarize_verified_rows(rows: list[dict]) -> dict:
    """Rows must already be SHA-verified against the retained source corpus."""
    if not rows:
        raise ValueError("no measured source poses")
    groups = defaultdict(list)
    role_of_mask = {}
    for row in rows:
        key = row.get("source_binary_mask_sha256")
        role = row.get("role")
        if not _hex64(key) or role not in ROLES:
            raise ValueError("unverified source pose group or role")
        if key in role_of_mask and role_of_mask[key] != role:
            raise ValueError("source binary silhouette crosses fit/diagnostic roles")
        role_of_mask[key] = role
        score = row.get("mask_iou")
        chamfer = row.get("boundary_chamfer_mean_physical_px")
        if (type(score) not in (int, float) or not 0 <= score <= 1 or
                type(chamfer) not in (int, float) or not 0 <= chamfer < 1e4):
            raise ValueError("invalid source silhouette measurement")
        groups[(role, key)].append(row)
    grouped = []
    for (role, key), members in sorted(groups.items()):
        grouped.append({
            "role": role, "source_binary_mask_sha256": key,
            "observation_count": len(members),
            "player_frame_ids": sorted(x["player"] + ":" + str(x["guest_frame"]) for x in members),
            "mean_mask_iou_for_same_source_shape": round(
                sum(x["mask_iou"] for x in members) / len(members), 8),
            "mean_boundary_chamfer_physical_px": round(
                sum(x["boundary_chamfer_mean_physical_px"] for x in members) / len(members), 8),
            "distinct_candidate_binary_masks": len({
                x["candidate_binary_mask_sha256"] for x in members
            }),
        })
    splits = {}
    for role in sorted(ROLES):
        relevant = [g for g in grouped if g["role"] == role]
        splits[role] = {
            "source_observation_count": sum(g["observation_count"] for g in relevant),
            "unique_original_silhouette_count": len(relevant),
            "equal_pose_weighted_mask_iou": (
                round(sum(g["mean_mask_iou_for_same_source_shape"] for g in relevant) / len(relevant), 8)
                if relevant else None),
            "equal_pose_weighted_boundary_chamfer_physical_px": (
                round(sum(g["mean_boundary_chamfer_physical_px"] for g in relevant) / len(relevant), 8)
                if relevant else None),
        }
    return {
        "observation_count": len(rows),
        "unique_source_binary_silhouette_count": len(grouped),
        "split_metrics": splits,
        "source_pose_groups": grouped,
        "source_silhouette_role_leakage": False,
        "one_weight_per_source_binary_silhouette": True,
        "diagnostic_split_is_independent_3d_camera_or_source_family": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def evaluate(manifest: Path) -> dict:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("unsupported multipose manifest schema")
    records = data.get("packets")
    if not isinstance(records, list) or not (1 <= len(records) <= 32):
        raise ValueError("required bounded set of 1..32 candidate pose packets")
    corpus = original_corpus()
    by_frame = {(x["player"], x["guest_frame"]): x for x in corpus["observations"]}
    rows, observed, one_scad_sha, packets_sha = [], set(), None, []
    root = manifest.resolve().parent
    for record in records:
        if not isinstance(record, dict) or record.get("role") not in ROLES:
            raise ValueError("each packet needs a declared fit/diagnostic role")
        path = _safe_file(root, record.get("packet_path"), ".json")
        if not _hex64(record.get("packet_sha256")):
            raise ValueError("packet SHA256 is required")
        raw = path.read_bytes()
        measured = _sha(raw)
        if measured != record["packet_sha256"]:
            raise ValueError("source-bound packet SHA256 mismatch")
        packet = json.loads(raw)
        if (packet.get("schema") != PACKET_SCHEMA or
                packet.get("shipping_art_approved") is not False or
                packet.get("owner_likeness_approved") is not False or
                packet.get("source_1994_3d_camera_verified") is not False):
            raise ValueError("packet is not an unapproved original-source research result")
        result = packet.get("silhouette_score")
        projection = packet.get("projected_alpha")
        if not isinstance(result, dict) or not isinstance(projection, dict):
            raise ValueError("source packet lacks scorer or projection")
        player, frame = result.get("player"), result.get("guest_frame")
        if type(frame) is not int or (player, frame) not in by_frame:
            raise ValueError("unsupported original sprite witness")
        if (player, frame) in observed:
            raise ValueError("duplicate player/frame pose would multiply an observation")
        observed.add((player, frame))
        source = by_frame[(player, frame)]
        if (result.get("source_rgba_sha256") != source["source_rgba_sha256"] or
                result.get("source_png_sha256") != source["png_file_sha256"] or
                packet.get("source_original_representation_id") != source["representation_id"]):
            raise ValueError("source frame/representation is not hash-bound to original pixels")
        if (not _hex64(packet.get("source_scad_sha256")) or
                not _hex64(packet.get("source_glb_sha256")) or
                not _hex64(packet.get("source_camera_manifest_sha256"))):
            raise ValueError("source model/camera evidence missing")
        if one_scad_sha is None:
            one_scad_sha = packet["source_scad_sha256"]
        if packet["source_scad_sha256"] != one_scad_sha:
            raise ValueError("multiple canonical models cannot share one multipose fit")
        image = _safe_file(root, record.get("candidate_path"), ".png")
        width, height, rgba, candidate_file_sha = decode_rgba_png(image)
        candidate_metrics = alpha_metrics(rgba, width, height)
        if (candidate_file_sha != packet.get("candidate_png_sha256") or
                candidate_file_sha != projection.get("candidate_png_sha256") or
                candidate_file_sha != result.get("candidate_png_sha256") or
                candidate_file_sha != record.get("candidate_png_sha256")):
            raise ValueError("candidate raster changed since projection/score")
        verified_score = score_retained_original(player, frame, image, candidate_file_sha, 4)
        if (verified_score.get("mask_iou") != result.get("mask_iou") or
                verified_score.get("boundary_chamfer_mean_physical_px") !=
                result.get("boundary_chamfer_mean_physical_px") or
                verified_score.get("mask_xor_pixels") != result.get("mask_xor_pixels")):
            raise ValueError("source packet score cannot be reproduced")
        rows.append({
            "player": player, "guest_frame": frame, "role": record["role"],
            "source_binary_mask_sha256": source["binary_mask_sha256"],
            "candidate_binary_mask_sha256": candidate_metrics["binary_mask_sha256"],
            "mask_iou": verified_score["mask_iou"],
            "boundary_chamfer_mean_physical_px": verified_score["boundary_chamfer_mean_physical_px"],
            "source_rgba_sha256": source["source_rgba_sha256"],
            "candidate_png_sha256": candidate_file_sha,
            "source_glb_sha256": packet["source_glb_sha256"],
            "source_camera_manifest_sha256": packet["source_camera_manifest_sha256"],
        })
        packets_sha.append(measured)
    summary = summarize_verified_rows(rows)
    return {
        "schema": REPORT_SCHEMA,
        "manifest_sha256": _sha(manifest.read_bytes()),
        "original_corpus_source_registry_sha256": corpus["source_registry_current_sha256"],
        "canonical_2026_unapproved_scad_sha256": one_scad_sha,
        "source_packet_shas": packets_sha,
        "verified_rows": rows,
        "no_source_1994_camera_or_3d_pose_certified": True,
        **summary,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = evaluate(args.manifest)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
