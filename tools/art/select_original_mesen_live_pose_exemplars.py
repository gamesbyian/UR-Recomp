#!/usr/bin/env python3
"""Choose deterministic REVIEW examples from 40 authenticated original 2D racers.

No 1994 3D pose labels, camera fitting, new fitting set, GLB promotion or
claim of a statistically blind holdout. Entire exact-8x8-content components
remain together, and authentic red is reflected only for screen-facing review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from tools.art.audit_original_mesen_sparse_pose_correspondence import (
    TICKS, SOURCE_ZIP_SHA, audit_source, validate_receipt,
)
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.audit_original_live40_historical_tile_novelty import (
    SCHEMA as LINEAGE_SCHEMA, exact_tiles, components,
)
from tools.art.no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-LIVE40-ORIGINAL-SCREEN-ORIENTED-COMPONENT-REVIEW/1"
SOURCE_ARTIFACT_ID = 13217381754
FROZEN_FIT_SOURCE = (1952, "blue")
FROZEN_WITHHELD_SOURCE = (1601, "red")
STATUS_CONNECTED = "historical_fit_tile_connected_review_only"
STATUS_DISJOINT = "historical_tile_disjoint_review_only"
# Independent SHA-authenticated five-archive audit #3094 freezes these exact
# original content-independent source identities, not merely group sizes.
FROZEN_DISJOINT_KEYS = frozenset({
    (1648, "blue"), (1671, "blue"), (1700, "blue"), (2011, "blue"),
    (1671, "red"), (1700, "red"), (1731, "red"), (2283, "blue"),
    (2445, "blue"),
})
RACERS = ("blue", "red")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def key_order(key: tuple[int, str]) -> tuple[int, int]:
    return (key[0], RACERS.index(key[1]))


def visible_mask(source: bytes, racer: str) -> bytes:
    """Player-visible original-source 2D alpha, never a model-fit flip search."""
    if (type(racer) is not str or racer not in RACERS
            or type(source) is not bytes or len(source) != 4096
            or any(v not in (0, 1) for v in source)):
        raise ValueError("authentic 64x64 binary source and blue/red identity required")
    return (b"".join(source[i:i+64][::-1] for i in range(0, 4096, 64))
            if racer == "red" else source)


def mask_iou(a: bytes, b: bytes) -> float:
    if (type(a) is not bytes or type(b) is not bytes or
            len(a) != 4096 or len(b) != 4096 or
            any(v not in (0, 1) for v in a+b)):
        raise ValueError("two binary original 64x64 source masks required")
    intersection = sum(x & y for x, y in zip(a, b))
    union = sum(x | y for x, y in zip(a, b))
    if not union:
        raise ValueError("zero-area source mask cannot establish 2D pose")
    return intersection / union


def select_one_component(keys: list[tuple[int, str]],
                         masks: dict[tuple[int, str], bytes]) -> dict:
    """Deterministic medoid, and a distant contrast iff component has >=4.

    Distance is 1-IoU of *screen-oriented* original binary source alpha.
    No GLB scoring, pose name, camera parameter, source time-order dynamics or
    historical role is an input to selection.
    """
    if (type(keys) is not list or not keys or len(keys) > 40 or
            len(set(keys)) != len(keys) or
            any(type(key) is not tuple or len(key) != 2 or
                type(key[0]) is not int or key[0] not in TICKS or
                key[1] not in RACERS or key not in masks for key in keys)):
        raise ValueError("invalid source-content component identities")
    for key in keys:
        visible_mask(masks[key], key[1])
        if not any(masks[key]):
            raise ValueError("empty original source sprite cannot anchor review")
    ordered = sorted(keys, key=key_order)
    pairs = {(a, b): mask_iou(visible_mask(masks[a], a[1]),
                            visible_mask(masks[b], b[1]))
             for a in ordered for b in ordered}
    if len(keys) == 1:
        medoid = ordered[0]
        contrast = None
        mean = minimum = None
        medoid_mean = 1.0
    else:
        means = {a: sum(pairs[a, b] for b in ordered if b != a) /
                 (len(ordered) - 1) for a in ordered}
        medoid = min(ordered, key=lambda k: (-means[k], key_order(k)))
        contrast = (min((k for k in ordered if k != medoid),
                        key=lambda k: (pairs[medoid, k], key_order(k)))
                    if len(ordered) >= 4 else None)
        values = [pairs[a, b] for i, a in enumerate(ordered)
                  for b in ordered[i+1:]]
        mean = round(sum(values) / len(values), 8)
        minimum = round(min(values), 8)
        medoid_mean = round(means[medoid], 8)
    return {
        "size": len(ordered),
        "members": [list(k) for k in ordered],
        "medoid": list(medoid),
        "contrast": list(contrast) if contrast else None,
        "mean_pairwise_visible_alpha_iou": mean,
        "min_pairwise_visible_alpha_iou": minimum,
        "medoid_average_visible_alpha_iou": medoid_mean,
    }


def select_live40(masks: dict[tuple[int, str], bytes],
                  planes: dict[tuple[int, str], bytes],
                  novelty: dict, registration: dict) -> dict:
    if (type(masks) is not dict or type(planes) is not dict or
            set(masks) != set(planes) or
            set(masks) != {(t, r) for t in TICKS for r in RACERS}):
        raise ValueError("all 40 source sprite identities required")
    if (type(novelty) is not dict or
            novelty.get("schema") != LINEAGE_SCHEMA or
            novelty.get("original_live_Mesen_source_zip_sha256") != SOURCE_ZIP_SHA or
            novelty.get("new_live_40_source_summary", {}).get("new_unclassified") != 38 or
            novelty.get("new_live_40_source_summary", {}).get("new_index_plane_tile_connected_components") != 11 or
            novelty.get("historical_fit_or_withheld_index_membership_modified") is not False or
            novelty.get("new_live_sources_assigned_a_fitting_or_holdout_role") is not False or
            novelty.get("owner_likeness_approved") is not False):
        raise ValueError("source historical tile-lineage authority invalid")
    validate_receipt(registration)
    frozen_joins = {(r["tick"], "blue" if r["slot"] == 96 else "red"):
                    r["frozen_role"] for r in registration["original_source_corpus_frozen_joins"]}
    if frozen_joins != {FROZEN_FIT_SOURCE: "fit", FROZEN_WITHHELD_SOURCE: "withheld"}:
        raise ValueError("historical original 16/19 source roles changed")
    for key in masks:
        visible_mask(masks[key], key[1])
        if (type(planes[key]) is not bytes or len(planes[key]) != 4096 or
                any(v > 15 for v in planes[key]) or
                bytes(1 if v else 0 for v in planes[key]) != masks[key]):
            raise ValueError("actual source 4bpp indices no longer reproduce original alpha")
    raw_groups = novelty.get("live_new_38_content_components")
    if type(raw_groups) is not list or len(raw_groups) != 11:
        raise ValueError("historical source tile-connected group census changed")
    groups = []
    used = set()
    component_input = []
    for raw in raw_groups:
        if (not isinstance(raw, dict) or
                type(raw.get("source_ticks_and_racers")) is not list or
                type(raw.get("shares_precommitted_fit_tile")) is not bool or
                raw.get("shares_precommitted_withheld_tile") is not False):
            raise ValueError("original tile group role malformed")
        keys = []
        for v in raw["source_ticks_and_racers"]:
            if (type(v) is not list or len(v) != 2 or
                    type(v[0]) is not int or v[1] not in RACERS):
                raise ValueError("invalid source sprite group membership")
            key = (v[0], v[1])
            if key not in masks or key in used or key in frozen_joins:
                raise ValueError("new source group leaked historical heldout or duplicate")
            used.add(key)
            keys.append(key)
            component_input.append({
                "tick": key[0], "racer": key[1],
                "tiles": exact_tiles(planes[key]),
                "shares_fit": raw["shares_precommitted_fit_tile"],
                "shares_withheld": False,
            })
        selected = select_one_component(keys, masks)
        selected["source_content_connection"] = (
            STATUS_CONNECTED if raw["shares_precommitted_fit_tile"] else STATUS_DISJOINT)
        selected["diagnostic_red_display_horizontal_mirror"] = True
        groups.append(selected)
    if (len(used) != 38 or used | set(frozen_joins) != set(masks)
            or sum(g["size"] for g in groups) != 38):
        raise ValueError("historical original fit/withheld/new 40 partition incomplete")
    independently_connected = components(component_input)
    normalized = {
        (tuple(tuple(x) for x in comp["original_ticks_and_racers"]),
         comp["has_exact_nonblank_tile_shared_with_precommitted_fit"])
        for comp in independently_connected
    }
    expected = {
        (tuple(tuple(x) for x in group["members"]),
         group["source_content_connection"] == STATUS_CONNECTED)
        for group in groups
    }
    if normalized != expected or len(normalized) != 11:
        raise ValueError("source original 8x8 tile components do not reproduce old classification")
    if (sorted(g["size"] for g in groups if g["source_content_connection"] == STATUS_DISJOINT)
            != [1, 4, 4] or
            {tuple(k) for g in groups if g["source_content_connection"] == STATUS_DISJOINT
             for k in g["members"]} != FROZEN_DISJOINT_KEYS):
        raise ValueError("historical-source-independent 4/4/1 identities altered")
    sample = {(r["tick"], racer): r[racer]
              for r in registration["samples"] for racer in RACERS}
    rows = []
    for key in sorted(masks, key=key_order):
        alpha = visible_mask(masks[key], key[1])
        pixels = [i for i, v in enumerate(alpha) if v]
        if len(pixels) != sample[key]["opaque"]:
            raise ValueError("source screen-owned alpha and provenance differ")
        xs = [p % 64 for p in pixels]
        ys = [p // 64 for p in pixels]
        rows.append({
            "tick": key[0],
            "racer": key[1],
            "original_source_index_sha256": sha(planes[key]),
            "original_source_alpha_sha256": sha(masks[key]),
            "screen_oriented_alpha_sha256": sha(alpha),
            "screen_origin_xy": sample[key]["screen_xy"],
            "player_visible_source_horizontal_mirror_applied": key[1] == "red",
            "source_opaque_pixels": len(pixels),
            "screen_oriented_source_bbox_xyxy": [min(xs), min(ys), max(xs), max(ys)],
            "old_frozen_role": frozen_joins.get(key, "unclassified"),
        })
    exemplars = sorted({tuple(v) for g in groups
                        for v in [g["medoid"], g["contrast"]] if v is not None},
                       key=key_order)
    visible = {k: visible_mask(masks[k], k[1]) for k in exemplars}
    pair_values = [mask_iou(visible[a], visible[b])
                   for i, a in enumerate(exemplars) for b in exemplars[i+1:]]
    return {
        "schema": SCHEMA,
        "actual_original_USA_ROM_source_zip_sha256": SOURCE_ZIP_SHA,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "original_emulator_ticks": list(TICKS),
        "orientation_basis": "completed original screen: red horizontally mirrored, blue unmirrored",
        "exemplar_algorithm": "source-alpha medoid per exact-tile component; max-distance contrast for size>=4; deterministic tie by tick then blue/red",
        "source_history_fit_and_withheld_unchanged": True,
        "new_live_source_fit_or_holdout_roles_assigned": False,
        "exemplars_prospectively_blind_to_2026_GLB_scores": False,
        "original_1994_pose_labels_verified": False,
        "original_source_3D_geometry_camera_bones_verified": False,
        "source_to_experimental_3D_GLb_pose_mapping_verified": False,
        "owner_likeness_approved": False,
        "historical_source_content_components": groups,
        "screen_oriented_review_exemplars": [list(x) for x in exemplars],
        "original_screen_registered_2D_observations": rows,
        "summary": {
            "actual_original_sprite_observations": 40,
            "historical_fit_examples_protected": 1,
            "historical_withheld_examples_protected": 1,
            "unclassified_new_source_observations": 38,
            "exact_tile_connected_components": 11,
            "content_independent_reference_only_groups": 3,
            "screen_oriented_review_exemplars": len(exemplars),
            "exemplar_mean_pairwise_alpha_iou": round(sum(pair_values)/len(pair_values), 8),
            "exemplar_min_pairwise_alpha_iou": round(min(pair_values), 8),
        },
    }


def evaluate(source_zip: Path, registration_path: Path, novelty_path: Path) -> dict:
    registration = json.loads(registration_path.read_text())
    novelty = json.loads(novelty_path.read_text())
    # Expensive source PPU/P6 forensic check is run once on the exact archive;
    # no ROM replay, new snapshot, or 3D renderer invocation.
    source = audit_source(source_zip, registration)
    if (source.get("actual_source_zip_sha256") != SOURCE_ZIP_SHA or
            source.get("source_pixel_accounting") !=
            {"opaque": 12937, "exact": 12416, "red_plus_13": 521} or
            source.get("unexplained_original_source_pixels") != 0):
        raise ValueError("original screen sprite pixel identity must remain exact")
    masks, planes = {}, {}
    with zipfile.ZipFile(source_zip) as original:
        for item in registration["samples"]:
            tick = item["tick"]
            oam = decode_oam(original.read(f"frame-{tick:06d}-oam.bin"))
            vram = original.read(f"frame-{tick:06d}-vram.bin")
            cgram = original.read(f"frame-{tick:06d}-cgram.bin")
            for racer, slot in (("blue", 96), ("red", 97)):
                obj = decode_source_obj(oam[slot], vram, cgram,
                    oam_mode=4, obj_base=0x6000, second_table_offset=0x1000)
                masks[tick, racer] = obj["alpha_mask"]
                planes[tick, racer] = obj["plane"]
    return select_live40(masks, planes, novelty, registration)



def committed_review_projection(result: dict) -> dict:
    """Small immutable source-derived receipt, without duplicating all 40 pixels."""
    return {key: result[key] for key in (
        "schema", "actual_original_USA_ROM_source_zip_sha256",
        "source_artifact_id", "orientation_basis", "exemplar_algorithm",
        "source_history_fit_and_withheld_unchanged",
        "new_live_source_fit_or_holdout_roles_assigned",
        "exemplars_prospectively_blind_to_2026_GLB_scores",
        "original_1994_pose_labels_verified",
        "original_source_3D_geometry_camera_bones_verified",
        "source_to_experimental_3D_GLb_pose_mapping_verified",
        "owner_likeness_approved",
        "historical_source_content_components",
        "screen_oriented_review_exemplars",
        "summary",
    )}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--registration", type=Path, default=Path(
        "analysis/data/racer-original-mesen-twenty-live-2d-screen-registrations-20261103.json"))
    parser.add_argument("--novelty", type=Path, default=Path(
        "analysis/data/racer-original-live40-historical-tile-content-novelty-20261103.json"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--verify-committed", type=Path)
    args = parser.parse_args()
    result = evaluate(args.source_zip, args.registration, args.novelty)
    if args.verify_committed:
        historic = json.loads(args.verify_committed.read_text())
        if historic != committed_review_projection(result):
            raise ValueError("recomputed authentic source exemplar selection differs")
    publish_text_once(args.out, json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({
        "authentic_original_screen_registered_sprite_count":
            result["summary"]["actual_original_sprite_observations"],
        "source_2D_review_exemplars":
            result["screen_oriented_review_exemplars"],
        "original_3D_pose_or_model_recovered": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
