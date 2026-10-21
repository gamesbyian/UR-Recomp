#!/usr/bin/env python3
"""Independent final-SDL proof of one native Modern root presentation motion.

Read four source/PE-bound screenshots already captured from separate processes
of the SAME real Windows binary. No raster fabrication, ROM reads, host writes,
time synthesis inside the game, or assertion of human/physical approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

CASES = (
    "root-motion-normal-zero",
    "root-motion-normal-eight",
    "root-motion-reduced-zero",
    "root-motion-reduced-eight",
)
SHA40 = re.compile(r"^[a-f0-9]{40}$")
SHA64 = re.compile(r"^[a-f0-9]{64}$")


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def load_case(folder: Path, name: str, source_sha: str) -> tuple[dict, bytes]:
    stage = folder / name
    if not stage.is_dir() or stage.is_symlink():
        raise ValueError("missing or symlinked native motion case: " + name)
    for filename in ("readback-receipt.json",
                     "probe_first/actual-sdl-drawable.pam",
                     "probe_first/native-process.log"):
        if (stage / filename).is_symlink():
            raise ValueError("symlinked original native evidence")
    receipt = json.loads((stage / "readback-receipt.json").read_text(encoding="utf-8"))
    p7 = (stage / "probe_first/actual-sdl-drawable.pam").read_bytes()
    log = (stage / "probe_first/native-process.log").read_bytes()
    if (receipt.get("native_semantic_route") != name or
            receipt.get("source_sha") != source_sha or
            receipt.get("execution_mode") != "modern" or
            receipt.get("native_process_exit") != 0 or
            receipt.get("SDL_driver") != "windows" or
            receipt.get("observed_in_draw") != 40 or
            receipt.get("native_process_log_sha256") != digest(log) or
            receipt.get("p7_sha256") != digest(p7) or
            not SHA64.fullmatch(str(receipt.get("exe_sha256", "")))):
        raise ValueError("mixed or invalid real native SDL motion provenance")
    dims = receipt.get("actual_sdl_renderer_output")
    if (not isinstance(dims, list) or len(dims) != 2 or
            any(type(d) is not int for d in dims) or
            not 320 <= dims[0] <= 3840 or not 224 <= dims[1] <= 2160 or
            receipt.get("requested_window_size") != dims):
        raise ValueError("actual native drawable geometry mismatch")
    head = (f"P7\nWIDTH {dims[0]}\nHEIGHT {dims[1]}\nDEPTH 4\n"
            "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
    if (not p7.startswith(head) or
            len(p7) != len(head) + dims[0] * dims[1] * 4):
        raise ValueError("incorrect or truncated original SDL P7 capture")
    if (b"UR_BALDOSA_MODERN_ROOT opened=1" not in log or
            b"UR_BALDOSA_MODERN_ROOT painted=1" not in log or
            f"output={dims[0]}x{dims[1]} source=SDL_RenderReadPixels".encode() not in log):
        raise ValueError("native root presentation/readback witness missing")
    return receipt, p7[len(head):]


def changed_rgb_pixels(a: bytes, b: bytes, width: int, height: int) -> dict:
    if len(a) != width * height * 4 or len(b) != len(a):
        raise ValueError("native readback pair size mismatch")
    changed = 0
    min_x = width
    min_y = height
    max_x = max_y = -1
    for p in range(width * height):
        offset = p * 4
        # Alpha can be zero on valid Windows SDL native RGB readbacks.
        if a[offset:offset + 3] == b[offset:offset + 3]:
            continue
        changed += 1
        x, y = p % width, p // width
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)
    return {
        "changed_rgb_pixels": changed,
        "changed_bbox_xyxy": ([min_x, min_y, max_x, max_y] if changed else None),
    }


def verify_four_real_native_motion_cases(folder: Path, source_sha: str) -> dict:
    if not SHA40.fullmatch(source_sha) or folder.is_symlink():
        raise ValueError("expected pinned current source and real evidence directory")
    receipts, images = {}, {}
    for name in CASES:
        receipts[name], images[name] = load_case(folder, name, source_sha)
    keys = ("source_sha", "exe_sha256", "actual_sdl_renderer_output",
            "requested_window_size", "observed_in_draw", "SDL_driver")
    for field in keys:
        if len({json.dumps(receipt[field]) for receipt in receipts.values()}) != 1:
            raise ValueError("native SDL captures must share one original source/PE/geometry")
    width, height = receipts[CASES[0]]["actual_sdl_renderer_output"]
    on = changed_rgb_pixels(images[CASES[0]], images[CASES[1]], width, height)
    off = changed_rgb_pixels(images[CASES[2]], images[CASES[3]], width, height)
    if on["changed_rgb_pixels"] == 0:
        raise ValueError("real final SDL output contains no menu motion pixels")
    if off["changed_rgb_pixels"] != 0:
        raise ValueError("reduced-motion real SDL output still moves")
    # This is evidence of UI-only pixel motion, not a proof of stock OBJ
    # shape, original racer cadence, aesthetic quality or physical display.
    return {
        "schema_version": 1,
        "status": "real native Windows SDL final-drawable motion pair, technical only",
        "source_sha": source_sha,
        "exe_sha256": receipts[CASES[0]]["exe_sha256"],
        "sdl_drawable": [width, height],
        "native_capture_draw": 40,
        "normal_0_to_8_tick_rgb": on,
        "reduced_0_to_8_tick_rgb": off,
        "source_guest_timing_independently_certified": False,
        "native_60hz_wall_clock_cadence_certified": False,
        "stock_cursor_obj_art_certified": False,
        "character_likeness_approved": False,
        "physical_hardware_approved": False,
        "release_gate_credit": 0,
        "case_p7_sha256": {n: receipts[n]["p7_sha256"] for n in CASES},
        "case_log_sha256": {n: receipts[n]["native_process_log_sha256"] for n in CASES},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_four_real_native_motion_cases(args.case_root, args.source_sha)
        if args.output.exists() or args.output.is_symlink():
            raise ValueError("do not overwrite earlier native motion evidence")
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print("NATIVE_FINAL_SDL_MENU_MOTION_AND_REDUCED_OK")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("NATIVE_FINAL_SDL_MOTION_REJECTED:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
