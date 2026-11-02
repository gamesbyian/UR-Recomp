#!/usr/bin/env python3
"""Bind experimental five-GLB costs to *verified* original-ROM source frames.

Source authentication is delegated to the existing pixel-checking corpus
validator. Missing masks fail closed. No pose identity or 3D camera is inferred.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.art.fit_original_racer_pose_sequence import fit
    from tools.art.freeze_racer_source_family_splits import CANONICAL_ROM_SHA, validate_corpus
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from fit_original_racer_pose_sequence import fit
    from freeze_racer_source_family_splits import CANONICAL_ROM_SHA, validate_corpus
    from no_replace_report import publish_text_once

POSES = ("upright", "pedal", "wheelie", "stunt", "bank")
MATRIX_SCHEMA = "UR-RACER-UNPAIRED-POSE-SIMILARITY-MATRIX/1"
SPLIT_SCHEMA = "UR-RACER-FROZEN-SOURCE-FAMILY-SPLIT/1"


def _sha(value):
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def build_input(corpus, matrix, requested_windows, split=None, corpus_sha=None):
    """Pure reduction; production must call validate_corpus on real source PNGs."""
    if (not isinstance(corpus, dict) or corpus.get("source_rom_sha256") != CANONICAL_ROM_SHA
            or corpus.get("source_rom_verified_and_used_for_composition") is not True):
        raise ValueError("not an authenticated canonical original USA ROM corpus")
    windows = corpus.get("registered_source_windows")
    if (not isinstance(windows, list) or not windows
            or not isinstance(requested_windows, list) or not requested_windows
            or len(set(requested_windows)) != len(requested_windows)
            or not set(requested_windows).issubset(set(windows))):
        raise ValueError("explicit valid source windows required")
    if (not isinstance(matrix, dict) or matrix.get("schema") != MATRIX_SCHEMA
            or matrix.get("source_original_rom_sha256") != CANONICAL_ROM_SHA
            or matrix.get("camera_status") != "provisional"
            or matrix.get("camera_shared_across_all_comparisons") is not True
            or matrix.get("similarities_are_unpaired_hypotheses_not_source_pose_mapping") is not True
            or matrix.get("per_pair_auto_alignment") is not False
            or matrix.get("registration_mode") not in ("fixed-witness", "source-registered")
            or not _sha(matrix.get("camera_manifest_sha256"))):
        raise ValueError("pose matrix is not source-bound/fixed-camera evidence")
    glbs = matrix.get("viewer_five_pose_glb_sha256")
    if (not isinstance(glbs, dict) or set(glbs) != set(POSES)
            or any(not _sha(value) for value in glbs.values())):
        raise ValueError("missing real five-pose GLB hashes")
    score_map = {}
    rows = matrix.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("missing actual original-source pose scores")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid source-mask row")
        mask, entries = row.get("source_binary_mask_sha256"), row.get("unpaired_pose_scores")
        if (not _sha(mask) or mask in score_map
                or not isinstance(entries, dict) or set(entries) != set(POSES)):
            raise ValueError("duplicated/missing original mask or pose")
        scored = {}
        for pose, entry in entries.items():
            iou = entry.get("mask_iou") if isinstance(entry, dict) else None
            if type(iou) not in (int, float) or not 0 <= iou <= 1:
                raise ValueError("invalid original mask score")
            scored[pose] = 1 - iou
        score_map[mask] = scored
    if len(score_map) != matrix.get("unique_original_binary_silhouettes"):
        raise ValueError("inconsistent source-mask score census")

    representations = corpus.get("source_representations")
    observations = corpus.get("source_temporal_frame_observations")
    if not isinstance(representations, dict) or not isinstance(observations, list):
        raise ValueError("missing original source registry")
    roles = {}
    if split is not None:
        if (not isinstance(split, dict) or not _sha(corpus_sha)
                or split.get("schema") != SPLIT_SCHEMA
                or split.get("source_rom_sha256") != CANONICAL_ROM_SHA
                or split.get("corpus_manifest_sha256") != corpus_sha
                or split.get("no_original_binary_silhouette_across_roles") is not True):
            raise ValueError("wrong or stale frozen original-source split")
        components = split.get("connected_window_components")
        if not isinstance(components, list):
            raise ValueError("missing original-source components")
        for group in components:
            role = group.get("role")
            if role not in ("fit", "diagnostic", "withheld_candidate"):
                raise ValueError("unknown original source role")
            for window in group.get("windows", []):
                if window in roles:
                    raise ValueError("duplicate source split window")
                roles[window] = role
        if set(roles) != set(windows):
            raise ValueError("split must cover every registered window")
        # Verify the source mask-disjointness independently rather than merely
        # trusting the frozen split's claimed boolean.
        assigned_masks = {}
        for observation in observations:
            role = roles[observation["window"]]
            for rid in observation["representations"].values():
                mask = representations[rid]["source_binary_mask_sha256"]
                previous = assigned_masks.setdefault(mask, role)
                if previous != role:
                    raise ValueError("identical original silhouette leaks across role splits")

    by_track, seen = {}, set()
    for observation in observations:
        window = observation.get("window")
        if window not in requested_windows:
            continue
        number, reps = observation.get("guest_frame"), observation.get("representations")
        if type(number) is not int or number < 0 or not isinstance(reps, dict) or not reps:
            raise ValueError("invalid original source frame")
        for player, rid in reps.items():
            identity = (window, player, number)
            if player not in ("p1", "p2") or identity in seen:
                raise ValueError("duplicate or incorrect original player/frame")
            seen.add(identity)
            info = representations.get(rid)
            if not isinstance(info, dict) or info.get("player") != player:
                raise ValueError("wrong-player original source representation")
            mask = info.get("source_binary_mask_sha256")
            if mask not in score_map:
                raise ValueError("missing actual 3D-pose score for source " + str(identity))
            by_track.setdefault((window, player), []).append((number, mask))
    if not by_track or set(window for window, _ in by_track) != set(requested_windows):
        raise ValueError("selected original source window has no observations")
    frames = []
    for (window, player), pairs in sorted(by_track.items()):
        previous = -1
        for number, mask in sorted(pairs):
            if number <= previous:
                raise ValueError("non-forward original guest-frame identity")
            previous = number
            frames.append({
                "window": window, "player": player, "guest_frame": number,
                "source_binary_mask_sha256": mask, "costs": score_map[mask],
            })
    return {
        "poses": list(POSES), "frames": frames, "change_penalty": 0.0,
        "provenance": {
            "original_rom_sha256": CANONICAL_ROM_SHA,
            "source_corpus_manifest_sha256": corpus_sha,
            "camera_manifest_sha256": matrix["camera_manifest_sha256"],
            "camera_registration_mode": matrix["registration_mode"],
            "five_original_experimental_glb_hashes": glbs,
            "source_mask_shas": sorted({f["source_binary_mask_sha256"] for f in frames}),
            "windows": sorted(requested_windows),
            "window_roles": {w: roles.get(w, "unfrozen_diagnostic") for w in sorted(requested_windows)},
            "original_1994_camera_or_pose_mapping_recovered": False,
        }
    }


def compute(corpus_path: Path, pose_matrix_path: Path, windows: list[str],
            split_path=None, change_penalty=0.0):
    corpus, checked = validate_corpus(corpus_path)
    raw = pose_matrix_path.read_bytes()
    matrix = json.loads(raw)
    split = json.loads(split_path.read_bytes()) if split_path else None
    inputs = build_input(corpus, matrix, windows, split, checked["corpus_sha256"])
    inputs["change_penalty"] = change_penalty
    result = fit(inputs)
    return {
        "schema": "UR-ART4K-SOURCE-BOUND-POSE-LABEL-EXPERIMENT/1",
        "actual_original_source_pngs_revalidated": True,
        "pose_matrix_report_sha256": hashlib.sha256(raw).hexdigest(),
        "provenance": inputs["provenance"], "frame_count": len(inputs["frames"]),
        "change_penalty": change_penalty, "temporal_experiment": result,
        "authentic_original_3d_pose_registration": False,
        "original_art_likeness_approved": False, "shipping_art_approved": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--pose-matrix", type=Path, required=True)
    parser.add_argument("--window", action="append", dest="windows", required=True)
    parser.add_argument("--frozen-split", type=Path)
    parser.add_argument("--change-penalty", type=float, default=0.0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = json.dumps(compute(args.corpus, args.pose_matrix, args.windows,
                                args.frozen_split, args.change_penalty),
                        sort_keys=True, indent=2) + "\n"
    if args.out:
        publish_text_once(args.out, result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
