#!/usr/bin/env python3
"""Cross-check historical source paint/wheel-disc morphology on real Mesen24.

Source-only retrospective cross-family observation. Reuses original high-chroma
classifier and tied grey-ring detector; it never creates a 3D part label,
selects an original/model wheel centre by fit, or edits a mesh.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from tools.art.audit_art4k_original_wheel_ring import (
    ORIGINAL_ROM_SHA256, ring_candidates,
)
from tools.art.audit_original_racer_chroma_components import source_chroma_pixels
from tools.art.audit_original_racer_paint_wheel_disc import disk_band_fractions
from tools.art.no_replace_report import publish_text_once
from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics

SCHEMA = "UR-ART4K-ORIGINAL-MESEN24-WHEEL-DISC-CHROMA-CROSSCHECK/1"
SOURCE_SCHEMA = "UR-ART4K-ORIGINAL-MESEN24-VIEWER-REFERENCE/1"
SOURCE_PPU_SHA = "28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
SOURCE_POSE_SHA = "6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20"
SOURCE_ROOT = "real-model-site/model-review/original-mesen24/"
ROLES = {"blue": ("p2", 96, 19), "red": ("p1", 97, 23)}
TICKS = tuple(range(1601, 1625))


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verified_manifest(packet: dict) -> dict:
    """Enforce the same original source identity as the existing Pages rail."""
    if (not isinstance(packet, dict) or packet.get("schema") != SOURCE_SCHEMA
            or packet.get("source_USA_ROM_sha256") != ORIGINAL_ROM_SHA256
            or packet.get("original_Mesen24_source_sha256") != SOURCE_PPU_SHA
            or packet.get("exact_original_ROM_pose_receipt_sha256") != SOURCE_POSE_SHA
            or packet.get("source_pixel_size") != [64, 64]
            or packet.get("display_pixel_aspect") != [7, 6]
            or packet.get("source_sprite_index_zero_transparent") is not True
            or packet.get("original_1994_3D_mesh_camera_pose_recovered") is not False
            or packet.get("original_source_to_2026_GLB_joint_pose_verified") is not False):
        raise ValueError("unaligned or unapproved original ROM/Mesen source")
    frames = packet.get("frames")
    if not isinstance(frames, list) or len(frames) != 48:
        raise ValueError("all 48 original Mesen PPU frames required")
    keyed = {}
    for rec in frames:
        if not isinstance(rec, dict):
            raise ValueError("invalid original PPU record")
        role, tick = rec.get("role"), rec.get("tick")
        if role not in ROLES or type(tick) is not int or tick not in TICKS:
            raise ValueError("unrecognized original source racer or tick")
        key = (role, tick)
        if key in keyed:
            raise ValueError("duplicate source role/tick")
        _, slot, _ = ROLES[role]
        frame_id, phase, direction = (
            rec.get("original_ROM_frame_ID"),
            rec.get("source_phase_index"),
            rec.get("source_orientation_index"),
        )
        if (rec.get("png") != f"{role}-{tick}.png"
                or rec.get("original_OAM_slot") != slot
                or type(frame_id) is not int or not 0 <= frame_id < 1536
                or type(phase) is not int or not 0 <= phase < 24
                or type(direction) is not int or not 0 <= direction < 64
                or frame_id != 64 * phase + direction):
            raise ValueError("wrong actual original ROM phase/orientation assignment")
        for field in ("png_sha256", "source_RGBA_sha256", "source_4bpp_plane_sha256"):
            value = rec.get(field)
            if not isinstance(value, str) or len(value) != 64 or any(
                    c not in "0123456789abcdef" for c in value):
                raise ValueError("missing exact original pixel source SHA: " + field)
        keyed[key] = rec
    if set(keyed) != {(role, tick) for role in ROLES for tick in TICKS}:
        raise ValueError("incomplete original two-racer 24-tick timeline")
    return keyed


def summarize_variants(observations: list, *, expected_shapes: dict) -> dict:
    """Exactly one vote per distinct alpha shape; preserve all RGB variants.

    Repeated chronology of the *same* PNG or identical alpha/paint never
    increases source model certainty. Within a shape, independent RGBA
    variants receive equal weight and all wheel-centre ties remain bounds.
    """
    if not isinstance(observations, list) or not observations:
        raise ValueError("missing source observations")
    per_role = defaultdict(lambda: defaultdict(dict))
    seen = set()
    for row in observations:
        role, tick = row.get("role"), row.get("tick")
        mask_sha, rgba_sha = row.get("binary_mask_sha256"), row.get("rgba_sha256")
        if (role not in expected_shapes or type(tick) is not int
                or (role, tick) in seen or not isinstance(mask_sha, str)
                or len(mask_sha) != 64 or not isinstance(rgba_sha, str)
                or len(rgba_sha) != 64):
            raise ValueError("invalid source shape/colour chronology")
        seen.add((role, tick))
        fractions = row.get("all_tied_source_wheel_disc_fractions")
        top = row.get("all_tied_source_at_or_below_ring_top_fractions")
        if (not isinstance(fractions, list) or not fractions
                or not isinstance(top, list) or len(fractions) != len(top)
                or any(type(x) not in (float, int) or not 0 <= x <= 1
                       for x in fractions + top)):
            raise ValueError("invalid tied source wheel-centre occupancy")
        descriptor = {
            "wheel_disc_low": min(fractions),
            "wheel_disc_high": max(fractions),
            "at_or_below_wheel_top_low": min(top),
            "at_or_below_wheel_top_high": max(top),
        }
        existing = per_role[role][mask_sha].get(rgba_sha)
        if existing is not None and existing != descriptor:
            raise ValueError("identical original RGBA varies by timeline tick")
        per_role[role][mask_sha][rgba_sha] = descriptor
    report = {}
    for role, count in expected_shapes.items():
        shapes = per_role.get(role, {})
        if not shapes or len(shapes) != count:
            raise ValueError("wrong original distinct alpha shape count for " + role)
        per_shape = []
        for variants in shapes.values():
            n = len(variants)
            per_shape.append({
                key: sum(v[key] for v in variants.values()) / n
                for key in ("wheel_disc_low", "wheel_disc_high",
                            "at_or_below_wheel_top_low",
                            "at_or_below_wheel_top_high")
            })
        report[role] = {
            "unique_original_binary_shapes_equal_vote": count,
            "original_rgba_variant_count": sum(len(v) for v in shapes.values()),
            "mean_source_chroma_inside_wheel_disc_low": round(
                sum(v["wheel_disc_low"] for v in per_shape) / count, 8),
            "mean_source_chroma_inside_wheel_disc_high": round(
                sum(v["wheel_disc_high"] for v in per_shape) / count, 8),
            "mean_source_chroma_at_or_below_wheel_top_low": round(
                sum(v["at_or_below_wheel_top_low"] for v in per_shape) / count, 8),
            "mean_source_chroma_at_or_below_wheel_top_high": round(
                sum(v["at_or_below_wheel_top_high"] for v in per_shape) / count, 8),
        }
    return report


def evaluate(source_zip: Path) -> dict:
    """Read the existing immutable real-model export artifact, no ROM re-run."""
    with ZipFile(source_zip) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate entries in authenticated original source ZIP")
        packet = json.loads(archive.read(SOURCE_ROOT + "source-poses.json"))
        records = verified_manifest(packet)
        observations = []
        with TemporaryDirectory(prefix="art4k-mesen24-paint-") as folder:
            temp = Path(folder)
            for (role, tick), rec in sorted(records.items()):
                path = SOURCE_ROOT + rec["png"]
                if path not in names:
                    raise ValueError("original Mesen PNG missing")
                original_png = archive.read(path)
                if sha(original_png) != rec["png_sha256"]:
                    raise ValueError("changed original Mesen PNG")
                temporary = temp / rec["png"]
                temporary.write_bytes(original_png)
                width, height, rgba, digest = decode_rgba_png(temporary)
                temporary.unlink()
                if ((width, height) != (64, 64) or digest != rec["png_sha256"]
                        or sha(rgba) != rec["source_RGBA_sha256"]):
                    raise ValueError("original source PNG/RGBA pixels or dimensions changed")
                metrics = alpha_metrics(rgba, width, height)
                pixels = source_chroma_pixels(rgba, ROLES[role][0])
                candidates = ring_candidates(rgba)
                fractions = disk_band_fractions(
                    pixels, candidates["best_candidate_centres_xy_radius_logical_px"])
                if candidates["max_neutral_ring_hits"] < 36:
                    raise ValueError("insufficient independent source ring pixels")
                observations.append({
                    "role": role, "tick": tick,
                    "source_png_sha256": digest,
                    "rgba_sha256": metrics["source_rgba_sha256"],
                    "binary_mask_sha256": metrics["binary_mask_sha256"],
                    "source_chroma_pixel_count": len(pixels),
                    "ring_centre_tie_count": len(fractions),
                    "all_tied_source_wheel_disc_fractions": [
                        x["fraction_inside_source_ring_disc"] for x in fractions],
                    "all_tied_source_at_or_below_ring_top_fractions": [
                        x["fraction_at_or_below_wheel_top"] for x in fractions],
                })
    summary = summarize_variants(
        observations, expected_shapes={role: spec[2] for role, spec in ROLES.items()})
    return {
        "schema": SCHEMA,
        "exact_original_USA_ROM_sha256": ORIGINAL_ROM_SHA256,
        "source_original_Mesen24_archive_sha256": SOURCE_PPU_SHA,
        "source_original_pose_receipt_sha256": SOURCE_POSE_SHA,
        "source_video_timeline_ticks": [1601, 1624],
        "source_png_rgba_and_alpha_each_verified": True,
        "original_racer_frames_verified": len(observations),
        "source_paint_classifier": "existing_original_classify_source_chroma",
        "source_ring_detector": "existing_all_tied_48sample_neutral_grey_ring",
        "source_wheel_radius_selected_by_art_model": False,
        "original_3d_anatomy_or_camera_recovered": False,
        "original_source_2d_views_prospective_blind_holdout": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
        "by_source_player": summary,
        "observations": observations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-artifact-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.source_artifact_zip)
    publish_text_once(args.out, json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("ART4K_MESEN24_SOURCE_PAINT_WHEEL_CROSSCHECK", json.dumps(
        report["by_source_player"], sort_keys=True))


if __name__ == "__main__":
    main()
