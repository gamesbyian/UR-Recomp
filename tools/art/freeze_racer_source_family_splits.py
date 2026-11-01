#!/usr/bin/env python3
"""Freeze leakage-free original-racer source family splits using actual pixel SHA.

Input is the PRIVATE immutable output of export_registered_original_racer_corpus.
This verifies each original PNG against its corpus receipt and groups all
windows sharing any source binary silhouette. A camera-independent 3D view is
NEVER inferred merely from a distinct ROM frame or alpha mask.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

try:
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
except ModuleNotFoundError:
    from racer_source_pixels import decode_rgba_png, alpha_metrics

CANONICAL_ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
CORPUS_SCHEMA = "UR-RACER-ROM-COMPOSED-SOURCE-CORPUS/1"
REQUEST_SCHEMA = "UR-RACER-SOURCE-FAMILY-SPLIT-REQUEST/1"
OUTPUT_SCHEMA = "UR-RACER-FROZEN-SOURCE-FAMILY-SPLIT/1"
ROLES = ("fit", "diagnostic", "withheld_candidate")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_corpus(path: Path) -> tuple[dict, dict]:
    source = path.read_bytes()
    corpus = json.loads(source)
    if (corpus.get("schema") != CORPUS_SCHEMA or
            corpus.get("source_rom_sha256") != CANONICAL_ROM_SHA or
            corpus.get("source_rom_verified_and_used_for_composition") is not True or
            corpus.get("owner_likeness_approved") is not False or
            corpus.get("shipping_art_approved") is not False):
        raise ValueError("corpus is not a canonical-ROM, unapproved source export receipt")
    windows = corpus.get("registered_source_windows")
    observations = corpus.get("source_temporal_frame_observations")
    representations = corpus.get("source_representations")
    if (not isinstance(windows, list) or not windows or
            len(set(windows)) != len(windows) or
            not isinstance(observations, list) or not observations or
            not isinstance(representations, dict) or not representations):
        raise ValueError("malformed original source corpus")
    windows_set = set(windows)
    for name in windows:
        if not isinstance(name, str) or not name:
            raise ValueError("invalid source window name")
    images = {}
    root = path.resolve().parent
    for rid, info in representations.items():
        if not isinstance(rid, str) or not isinstance(info, dict) or info.get("player") not in ("p1","p2"):
            raise ValueError("unregistered player or malformed representation")
        pixel_sha = info.get("source_rgba_sha256")
        if not isinstance(pixel_sha, str) or len(pixel_sha) != 64 or any(c not in "0123456789abcdef" for c in pixel_sha):
            raise ValueError("missing authentic decoded RGBA hash")
        expected = f"stock/source-{pixel_sha}.png"
        if info.get("local_file") != expected:
            raise ValueError("untrusted or swapped original source PNG location")
        file = (root / expected).resolve()
        if not file.is_relative_to(root) or not file.is_file():
            raise ValueError("missing or escaped private source PNG")
        if expected not in images:
            w, h, rgba, file_hash = decode_rgba_png(file)
            if (w, h) != (64, 64):
                raise ValueError("registered ROM source must remain 64x64")
            images[expected] = (file_hash, alpha_metrics(rgba, w, h))
        file_hash, measured = images[expected]
        for key in ("source_rgba_sha256", "source_alpha_sha256", "source_binary_mask_sha256"):
            if info.get(key) != measured[key if key != "source_binary_mask_sha256" else "binary_mask_sha256"]:
                raise ValueError("original source RGBA/alpha/binary mask hash mismatch")
        if (info.get("local_png_sha256") != file_hash or
                info.get("source_opaque_pixels") != measured["nonzero_alpha_pixels"] or
                info.get("source_alpha_bbox_xyxy") != measured["alpha_bbox_xyxy_inclusive"]):
            raise ValueError("source original mask geometry or PNG SHA mismatch")
    seen = set()
    per_window = defaultdict(set)
    for frame in observations:
        if not isinstance(frame, dict) or frame.get("window") not in windows_set or type(frame.get("guest_frame")) is not int:
            raise ValueError("unsupported temporal window/frame")
        identities = frame.get("representations")
        if not isinstance(identities, dict) or not identities:
            raise ValueError("source frame has no original racer")
        key = (frame["window"], frame["guest_frame"])
        if key in seen:
            raise ValueError("duplicate registered source frame in window")
        seen.add(key)
        for player, rid in identities.items():
            if player not in ("p1", "p2") or rid not in representations or representations[rid]["player"] != player:
                raise ValueError("source frame has unknown/wrong-player identity")
            per_window[frame["window"]].add(representations[rid]["source_binary_mask_sha256"])
    if set(per_window) != windows_set:
        raise ValueError("one or more original source windows have no records")
    if corpus.get("unique_representations") != len(representations):
        raise ValueError("source identity count is stale")
    if corpus.get("unique_rgba_images") != len(images):
        raise ValueError("source pixel image count is stale")
    grouped = set().union(*per_window.values())
    if corpus.get("unique_binary_silhouettes") != len({
        x["source_binary_mask_sha256"] for x in representations.values()
    }):
        raise ValueError("source binary silhouette group count is stale")
    return corpus, {"corpus_sha256": digest(source), "per_window_masks": per_window,
                    "verified_png_count": len(images), "all_masks": grouped}


def freeze(corpus_path: Path, request_path: Path) -> dict:
    corpus, validated = validate_corpus(corpus_path)
    raw = request_path.read_bytes()
    request = json.loads(raw)
    roles = request.get("roles")
    names = set(corpus["registered_source_windows"])
    if (request.get("schema") != REQUEST_SCHEMA or
            not isinstance(roles, dict) or set(roles) != names or
            any(role not in ROLES for role in roles.values())):
        raise ValueError("every source window requires one explicit valid role")
    mask_to_windows = defaultdict(set)
    for window, masks in validated["per_window_masks"].items():
        for sha in masks:
            mask_to_windows[sha].add(window)
    parent = {name: name for name in names}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def unite(a, b):
        parent[find(a)] = find(b)

    for same_mask_windows in mask_to_windows.values():
        first = min(same_mask_windows)
        for name in same_mask_windows:
            unite(first, name)
    components = defaultdict(set)
    for name in names:
        components[find(name)].add(name)
    output_components, assigned_masks = [], {}
    for member_set in sorted(components.values(), key=lambda x: sorted(x)):
        component_roles = {roles[n] for n in member_set}
        if len(component_roles) != 1:
            raise ValueError("original source binary silhouette leaks across split roles: " +
                             ",".join(sorted(member_set)))
        role = next(iter(component_roles))
        union = set().union(*(validated["per_window_masks"][n] for n in member_set))
        for h in union:
            if h in assigned_masks:
                raise ValueError("duplicate original silhouette across source partitions")
            assigned_masks[h] = role
        output_components.append({
            "windows": sorted(member_set),
            "role": role,
            "unique_source_binary_silhouette_count": len(union),
            "source_binary_mask_shas": sorted(union),
        })
    counts = {
        role: {
            "window_count": sum(len(c["windows"]) for c in output_components if c["role"] == role),
            "independent_binary_silhouette_group_count": sum(
                c["unique_source_binary_silhouette_count"]
                for c in output_components if c["role"] == role
            ),
        }
        for role in ROLES
    }
    return {
        "schema": OUTPUT_SCHEMA,
        "corpus_manifest_sha256": validated["corpus_sha256"],
        "split_request_sha256": digest(raw),
        "source_rom_sha256": CANONICAL_ROM_SHA,
        "independently_revalidated_source_png_count": validated["verified_png_count"],
        "total_source_windows": len(names),
        "verified_distinct_original_binary_silhouettes": len(validated["all_masks"]),
        "connected_window_components": output_components,
        "role_summary": counts,
        "no_original_binary_silhouette_across_roles": True,
        "source_family_split_is_frozen_by_exact_input_hashes": True,
        "withheld_candidate_is_an_independent_3d_camera": False,
        "source_1994_camera_recovered": False,
        "source_3d_pose_mapping_verified": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("private_corpus", type=Path, help="immutable source-corpus.json")
    ap.add_argument("roles", type=Path, nargs="?", help="exact window-to-role request JSON")
    ap.add_argument("--template", action="store_true",
                    help="print a conservative all-diagnostic request template, to edit privately")
    args = ap.parse_args()
    if args.template:
        if args.roles is not None:
            ap.error("do not supply roles when requesting a template")
        manifest, _ = validate_corpus(args.private_corpus)
        template = {"schema": REQUEST_SCHEMA,
                    "roles": {name: "diagnostic" for name in
                              sorted(manifest["registered_source_windows"])}}
        print(json.dumps(template, indent=2, sort_keys=True))
        return
    if args.roles is None:
        ap.error("roles JSON required, or use --template")
    print(json.dumps(freeze(args.private_corpus, args.roles), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
