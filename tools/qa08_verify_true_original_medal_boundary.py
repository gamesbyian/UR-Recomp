#!/usr/bin/env python3
"""QA08: first real original medal pose transition, not a video-frame shift.

Reuses two independent fail-closed original/native verifiers already merged
in main. Measures source-internal fields only, after proving that real 2014
callback f-1 corresponds to original painter f-1. No guest/rendering edits.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import tempfile
import zipfile

try:
    from tools import qa08_verify_original_medal_callback_registration as callbacks
    from tools import qa08_verify_original_native_medal_owners as owners
except ImportError:  # direct tools/foo.py invocation
    import qa08_verify_original_medal_callback_registration as callbacks
    import qa08_verify_original_native_medal_owners as owners

ORIGINAL_OUTER_SHA = "3475ee87b5b20768f9377d8d1c787927955c33ee6d4388dae008f5486a81370e"
ORIGINAL_NESTED_SHA = callbacks.ORIGINAL_ZIP_SHA
SOURCE_FRAMES = (4032, 4176)
POINTS = owners.POINTS


def signature_table(painter_zip: Path) -> dict[tuple[int, int, int], tuple]:
    """Every original field has two separate paint passes and one final stage."""
    raw_stages = owners.member(painter_zip, owners.ORIGINAL_SHA, owners.ORIGINAL_LAYERS)
    raw_calls = owners.member(painter_zip, owners.ORIGINAL_SHA, owners.ORIGINAL_CALLS)
    stages = raw_stages.decode("ascii").splitlines()
    calls = raw_calls.decode("ascii").splitlines()
    if len(stages) != 360 or len(calls) != 252:
        raise ValueError("genuine original stage/tile populations changed")
    finals = {}
    for line in stages:
        d = owners.decode(line, "UR_QA08_ORIGINAL_MEDAL_LAYER")
        if d["range"] != "0,223" or d["bgmode"] != "3":
            raise ValueError("original painter geometry/mode changed")
        if d["stage"] != "FINAL":
            continue
        key = int(d["frame"]), int(d["x"]), int(d["y"])
        if key in finals:
            raise ValueError("original final stage duplicated")
        finals[key] = (int(d["depth"], 16), int(d["rgb565"], 16))
    if len(finals) != 90:
        raise ValueError("source original final-stage observations incomplete")
    raw_writers = {}
    for line in calls:
        d = owners.decode(line, "UR_QA08_ORIGINAL_ACTIVE_MEDAL_TILE")
        key = int(d["frame"]), int(d["x"]), int(d["y"])
        raw_writers.setdefault(key, []).append(d)
    result = {}
    for key, (depth, colour) in finals.items():
        both = raw_writers.get(key, ())
        if len(both) not in (2, 4):
            raise ValueError("original painter must execute two identical source passes")
        mid = len(both) // 2
        token = lambda d: (d["slot"], d["src_tile"], d["changed_z"])
        if list(map(token, both[:mid])) != list(map(token, both[mid:])):
            raise ValueError("separately executed original painter passes diverged")
        contributing = [d for d in both[:mid] if d["changed_z"] == "1"]
        if len(contributing) > 1:
            raise ValueError("multiple claimed original last-writer changes")
        if not contributing:
            if depth != 0x27:
                raise ValueError("BG0 negative control did not survive source background")
            result[key] = (depth, colour, None, None)
        else:
            if depth != 0x28:
                raise ValueError("visible source sprite lost after original background painters")
            winner = contributing[0]
            result[key] = (
                depth, colour, int(winner["slot"]), int(winner["src_tile"], 16)
            )
    return result


def true_source_boundary(signatures: dict, first: int, pts=POINTS) -> list[dict]:
    """Prove three field plateau, discontinuity, three field plateau, next flip."""
    rows = []
    for x, y in pts:
        try:
            prior = [signatures[(f, x, y)] for f in range(first - 3, first)]
            after = [signatures[(f, x, y)] for f in range(first, first + 3)]
            following = signatures[(first + 3, x, y)]
        except KeyError as exc:
            raise ValueError("missing original field around first pose transition") from exc
        if len(set(prior)) != 1 or len(set(after)) != 1:
            raise ValueError("original three-field pose stability not observed")
        if prior[-1] == after[0] or following == after[-1]:
            raise ValueError("original source pose onset or following flip disappeared")
        before, now = prior[-1], after[0]
        rows.append({
            "source_internal_previous": first - 1,
            "original_actual_callback_label": first - 1,
            "source_internal_first_new_pose": first,
            "source_internal_first_next_pose": first + 3,
            "point": [x, y],
            "prior_final_depth": f"{before[0]:02x}",
            "after_final_depth": f"{now[0]:02x}",
            "prior_source_rgb565": f"{before[1]:04x}",
            "after_source_rgb565": f"{now[1]:04x}",
            "prior_actual_winner_slot": before[2],
            "after_actual_winner_slot": now[2],
            "prior_source_tile": None if before[3] is None else f"{before[3]:04x}",
            "after_source_tile": None if now[3] is None else f"{now[3]:04x}",
        })
    return rows


def verify(original_outer: Path, painter: Path, native_4bpp: Path) -> dict:
    # The original video SHA, callback count, actually consumed original inputs,
    # and original painter-to-same-callback pixels are independently validated.
    raw = original_outer.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_OUTER_SHA:
        raise ValueError("2014 original source bundle identity changed")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise ValueError("original source ZIP member CRC failed")
        original = z.read("original.zip")
    if hashlib.sha256(original).hexdigest() != ORIGINAL_NESTED_SHA:
        raise ValueError("nested original 263-callback image identity changed")
    with tempfile.TemporaryDirectory() as tmp:
        source_path = Path(tmp) / "original.zip"
        source_path.write_bytes(original)
        callback_result = callbacks.verify(source_path, painter)
    if callback_result["matched_pixels"] != 10 or callback_result["wrong_pixels"] != 0:
        raise ValueError("real original painter does not match its own video callbacks")
    native_result = owners.verify(painter, native_4bpp)
    if (native_result["original_sprite_pixels_matching_native_slot_and_tile_suffix"] != 8
            or native_result["original_native_background_negative_controls"] != 2):
        raise ValueError("physical native 4bpp ownership not source-matched")
    table = signature_table(painter)
    rows = []
    for first in SOURCE_FRAMES:
        rows.extend(true_source_boundary(table, first))
    if len(rows) != 10:
        raise ValueError("original pose transition sample count changed")
    if [tuple(table[(f, *point)]) for point in POINTS for f in SOURCE_FRAMES[0:1]] != [
        tuple(table[(SOURCE_FRAMES[1], *point)]) for point in POINTS
    ]:
        raise ValueError("source's observed 144-field repeat changed")
    return {
        "schema": "qa08-genuine-original-medal-first-pose-3-field-boundary/1",
        "original_2014_outer_sha256": ORIGINAL_OUTER_SHA,
        "original_painter_sha256": owners.ORIGINAL_SHA,
        "native_physical_4bpp_sha256": owners.NATIVE_SHA,
        "source_original_painter_callback_exact_pixels": 10,
        "source_original_first_boundary_changes": len(rows),
        "original_three_field_plateaus": 4,
        "original_144_field_pose_recurrence": True,
        "native_actual_matching_source_internal_OBJ": 8,
        "native_actual_matching_source_internal_BG": 2,
        "source_original_native_consumed_input_and_beam_proven": False,
        "global_frame_shift_permitted": False,
        "original_native_correct_callback_RGB5_parity_proven": False,
        "release_acceptance": False,
        "source_internal_transitions": rows,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-outer", required=True, type=Path)
    p.add_argument("--original-painter", required=True, type=Path)
    p.add_argument("--native-4bpp", required=True, type=Path)
    p.add_argument("--out", type=Path)
    opts = p.parse_args()
    try:
        result = verify(opts.original_outer, opts.original_painter, opts.native_4bpp)
    except (OSError, ValueError, KeyError, UnicodeError, zipfile.BadZipFile) as exc:
        p.exit(2, f"QA08_SOURCE_MEDAL_BOUNDARY_REFUSED: {exc}\n")
    report = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if opts.out:
        opts.out.write_text(report, encoding="utf-8")
    else:
        print(report)
    print("QA08_TRUE_MEDAL_BOUNDARY_OK original=10/10 native_OBJ=8/8 BG=2/2")


if __name__ == "__main__":
    main()
