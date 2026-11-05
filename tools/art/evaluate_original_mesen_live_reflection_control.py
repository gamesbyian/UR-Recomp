#!/usr/bin/env python3
"""ROM-free, exact-receipt 2D model-reflection control for the 40 live original sprites.

A fixed horizontal reflection of the *registered 2D candidate* and of the
original held red source leaves binary IoU invariant. The held-source score is
therefore exactly the original displayed-red versus reflected-candidate score.
This is a mathematical projection control, not a rerendered or fitted 3D rig.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from tools.art.audit_original_mesen_sparse_pose_correspondence import TICKS
from tools.art.no_replace_report import publish_text_once

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "analysis/data"
BLOBS = {
    "racer-original-live20-five-real-glb-unpaired-diagnostic-20261103.json":
        "8cbc4d56326da4f41751c66535a304d758051eea",
    "racer-original-live20-screen-orientation-sensitivity-20261103.json":
        "1bc1e7a4a6777d83972621398ef631a752140bc0",
    "racer-original-live40-screen-review-exemplars-20261103.json":
        "256807c0edbc3059a49b9232d642ee025a3fb0c7",
}
SOURCE_ZIP_SHA = "709fbc2a1cd94b888d8ae0d43894c42c5d455bd968f6bc11f26e710f44e2788f"
CAMERA_SHA = "1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
POSES = ("upright", "pedal", "wheelie", "stunt", "bank")
SCHEMA = "UR-ART4K-LIVE40-FIXED-REGISTERED-2D-REFLECTION-CONTROL/1"


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def frozen_inputs() -> tuple[dict, dict, dict]:
    packets = []
    for name, expected in BLOBS.items():
        raw = (DATA / name).read_bytes()
        # Git may check text receipts out with CRLF on Windows. Hash their
        # canonical LF bytes while still rejecting substantive modifications.
        canonical = raw.replace(b"\r\n", b"\n")
        if git_blob_sha(canonical) != expected:
            raise ValueError(f"frozen original/model receipt changed: {name}")
        packets.append(json.loads(raw))
    return tuple(packets)


def reflect64(mask: bytes) -> bytes:
    """Pixel-exact screen reflection about x=31.5, not an optimizer."""
    if type(mask) is not bytes or len(mask) != 4096 or set(mask) - {0, 1}:
        raise ValueError("reflection needs binary 64x64 raster")
    return b"".join(mask[i:i+64][::-1] for i in range(0, 4096, 64))


def lowest_alpha_x2(mask: bytes) -> int:
    if type(mask) is not bytes or len(mask) != 4096 or set(mask) - {0, 1} or not any(mask):
        raise ValueError("anchor needs nonempty binary 64x64 raster")
    y = max(i // 64 for i, v in enumerate(mask) if v)
    xs = [i % 64 for i, v in enumerate(mask) if v and i // 64 == y]
    return min(xs) + max(xs)


def iou(a: bytes, b: bytes) -> float:
    if (type(a) is not bytes or type(b) is not bytes or
            len(a) != 4096 or len(b) != 4096 or
            set(a) - {0, 1} or set(b) - {0, 1}):
        raise ValueError("IoU needs binary 64x64 rasters")
    union = sum(x | y for x, y in zip(a, b))
    if not union:
        raise ValueError("empty union")
    return sum(x & y for x, y in zip(a, b)) / union


def _score_map(value: dict) -> None:
    if (type(value) is not dict or set(value) != set(POSES) or
            any(type(x) not in (int, float) or not math.isfinite(x) or
                not 0 <= x <= 1 for x in value.values())):
        raise ValueError("incomplete/invalid immutable five-GLB score row")


def _mean(values) -> float:
    values = list(values)
    if not values:
        raise ValueError("empty comparison stratum")
    return round(sum(values) / len(values), 8)


def _summarize(rows: list[dict]) -> dict:
    return {
        "observations": len(rows),
        "shared_model_projection_mean_best_of_five_iou": _mean(
            max(row["shared"].values()) for row in rows),
        "red_model_projection_reflected_mean_best_of_five_iou": _mean(
            max(row["reflected"].values()) for row in rows),
    }


def evaluate(base: dict, screen: dict, refs: dict) -> dict:
    if (base.get("schema") != "UR-ART4K-ORIGINAL-LIVE20-REAL-FIVE-GLB-UNPAIRED-SCORE-RECEIPT/1" or
            screen.get("schema") != "UR-ART4K-LIVE20-RED-SCREEN-FACING-VS-HELD-UNPAIRED-REAL-GLB/1" or
            refs.get("schema") != "UR-ART4K-LIVE40-ORIGINAL-SCREEN-ORIENTED-COMPONENT-REVIEW/1" or
            base.get("source_original_zip_sha256") != SOURCE_ZIP_SHA or
            screen.get("original_source_zip_sha256") != SOURCE_ZIP_SHA or
            refs.get("actual_original_USA_ROM_source_zip_sha256") != SOURCE_ZIP_SHA or
            base.get("source_original_artifact_id") != 13217381754 or
            screen.get("original_source_artifact_id") != 13217381754 or
            refs.get("source_artifact_id") != 13217381754 or
            base.get("provisional_P1_1205_camera_sha256") != CAMERA_SHA or
            screen.get("common_provisional_camera_sha256") != CAMERA_SHA or
            base.get("real_2026_GLb_sha256") != screen.get("real_2026_five_GLb_sha256") or
            set(base.get("real_2026_GLb_sha256", {})) != set(POSES) or
            screen.get("original_red_display_reflection_independently_source_screen_authenticated") is not True or
            screen.get("original_blue_display_reflection") is not False or
            refs.get("source_history_fit_and_withheld_unchanged") is not True or
            refs.get("new_live_source_fit_or_holdout_roles_assigned") is not False or
            base.get("old_frozen_index_plane_roles_among_new_live_sources") != {
                "fit": 1, "withheld": 1, "strict_withheld": 0, "unclassified_live_source": 38}):
        raise ValueError("inconsistent original source, camera, model or historical role evidence")

    original = base.get("per_original_racer_frame_scores")
    red_rows = screen.get("red_screen_oriented_fixed_camera_unpaired_20_rows")
    expected = {(tick, racer) for tick in TICKS for racer in ("blue", "red")}
    if (type(original) is not list or len(original) != 40 or
            type(red_rows) is not list or len(red_rows) != 20):
        raise ValueError("incomplete source census")
    red = {}
    for entry in red_rows:
        tick = entry.get("tick")
        if (tick not in TICKS or tick in red or
                entry.get("completed_screen_reflection_from_held") is not True or
                entry.get("completed_screen_racer") != "red"):
            raise ValueError("not source-attested red completed-screen orientation")
        _score_map(entry.get("screen_oriented_iou_by_glb_pose"))
        red[tick] = entry["screen_oriented_iou_by_glb_pose"]
    if set(red) != set(TICKS):
        raise ValueError("missing red original screen tick")

    rows = {}
    roles = Counter()
    for entry in original:
        key = (entry.get("original_mesen_tick"), entry.get("original_racer"))
        if key not in expected or key in rows:
            raise ValueError("duplicate or unknown original observed racer/tick")
        held = entry.get("fixed_camera_iou_by_GLb_pose")
        _score_map(held)
        top = max(held.values())
        tied = [p for p in POSES if held[p] == top]
        if (entry.get("unique_unpaired_pose_winner") !=
                (tied[0] if len(tied) == 1 else None) or
                entry.get("ambiguous_equal_iou_candidates") !=
                (tied if len(tied) > 1 else [])):
            raise ValueError("held original real-GLB ranking receipt changed")
        racer = key[1]
        role = entry.get("frozen_role")
        if role not in ("fit", "withheld", "strict_withheld", "unclassified_live_source"):
            raise ValueError("original frozen source role invalid")
        roles[role] += 1
        # Fixed 2D model projection mirrored on RED ONLY. If R denotes
        # horizontal reflection, IoU(R(source), R(candidate)) equals
        # IoU(source, candidate). The held-source IoUs are therefore
        # re-used EXACTLY, not guessed GLB renders or camera refits.
        rows[key] = {
            "shared": red[key[0]] if racer == "red" else held,
            "reflected": held, "role": role, "racer": racer,
        }
    if set(rows) != expected or dict(roles) != {
            "fit": 1, "withheld": 1, "unclassified_live_source": 38}:
        raise ValueError("source census or frozen source roles modified")

    groups = refs.get("historical_source_content_components")
    if type(groups) is not list or len(groups) != 11:
        raise ValueError("unverified source tile-content components")
    claimed = set()
    balanced = []
    for component in groups:
        members = component.get("members")
        if (type(members) is not list or len(members) != component.get("size")):
            raise ValueError("bad original content group cardinality")
        current = []
        for pair in members:
            if type(pair) is not list or len(pair) != 2:
                raise ValueError("malformed source content membership")
            key = tuple(pair)
            if (key not in rows or key in claimed or
                    rows[key]["role"] != "unclassified_live_source"):
                raise ValueError("unfrozen/duplicated historical content group")
            claimed.add(key)
            current.append(rows[key])
        balanced.append(_summarize(current))
    if claimed != {k for k, row in rows.items()
                   if row["role"] == "unclassified_live_source"}:
        raise ValueError("unclassified source components are incomplete")

    group_deltas = [
        x["red_model_projection_reflected_mean_best_of_five_iou"] -
        x["shared_model_projection_mean_best_of_five_iou"] for x in balanced
    ]
    all_rows = [rows[(t, r)] for t in TICKS for r in ("blue", "red")]
    result = {
        "schema": SCHEMA,
        "original_source_zip_sha256": SOURCE_ZIP_SHA,
        "frozen_receipt_git_blob_sha1": BLOBS,
        "camera_sha256": CAMERA_SHA,
        "real_2026_glb_sha256": base["real_2026_GLb_sha256"],
        "arms": {
            "shared_model_projection": "original completed screen, same fixed 2D model projection both players",
            "red_model_projection_reflected": "original completed screen; registered 64px candidate horizontally reflected for red only",
        },
        "by_player": {r: _summarize([z for z in all_rows if z["racer"] == r])
                      for r in ("blue", "red")},
        "all_40_raw_observations": _summarize(all_rows),
        "unclassified_38_diagnostic_only": _summarize(
            [z for z in all_rows if z["role"] == "unclassified_live_source"]),
        "unclassified_11_content_component_equal_weight": {
            "groups": len(balanced),
            "shared_model_projection_mean_best_of_five_iou": _mean(
                x["shared_model_projection_mean_best_of_five_iou"] for x in balanced),
            "red_model_projection_reflected_mean_best_of_five_iou": _mean(
                x["red_model_projection_reflected_mean_best_of_five_iou"] for x in balanced),
            "improved_groups": sum(d > 0 for d in group_deltas),
            "worsened_groups": sum(d < 0 for d in group_deltas),
            "unchanged_groups": sum(d == 0 for d in group_deltas),
        },
        "historical_roles_preserved": {
            "fit": 1, "withheld": 1, "strict_withheld": 0, "unclassified": 38},
        "per_frame_best_of_five_is_optimistic_unpaired_oracle": True,
        "per_frame_camera_refit_or_pose_parameter_optimization": False,
        "new_original_emulator_or_glb_render_executed": False,
        "source_to_2026_glb_pose_mapping_verified": False,
        "original_1994_camera_rig_geometry_recovered": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="optional no-overwrite JSON report")
    args = parser.parse_args()
    report = evaluate(*frozen_inputs())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
