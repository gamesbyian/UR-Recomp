#!/usr/bin/env python3
"""Independent final-Windows-SDL evidence for real native title -> Modern root.

Read untouched P7 SDL_RenderReadPixels and native process logs from the
existing Baldosa/UR Windows PE. This tool paints nothing, invents no source
frames or guest inputs, and cannot confer artwork/hardware/release approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

CASES = ("title-still", "title-entered-root",
         "title-reduced-still", "title-reduced-entered-root")
SHA40 = re.compile(r"^[a-f0-9]{40}$")
SHA64 = re.compile(r"^[a-f0-9]{64}$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_real_case(root: Path, name: str, expected_source: str):
    stage = root / name
    if not stage.is_dir() or stage.is_symlink():
        raise ValueError("missing or redirected original Windows title case " + name)
    names = ("readback-receipt.json",
             "probe_first/actual-sdl-drawable.pam",
             "probe_first/native-process.log")
    if any((stage / n).is_symlink() for n in names):
        raise ValueError("symlinked title evidence")
    receipt = json.loads((stage / names[0]).read_text(encoding="utf-8"))
    raster = (stage / names[1]).read_bytes()
    log = (stage / names[2]).read_bytes()
    if (receipt.get("source_sha") != expected_source or
            receipt.get("native_semantic_route") != name or
            receipt.get("native_process_exit") != 0 or
            receipt.get("execution_mode") != "modern" or
            receipt.get("SDL_driver") != "windows" or
            receipt.get("observed_in_draw") != 40 or
            receipt.get("native_process_log_sha256") != sha(log) or
            receipt.get("p7_sha256") != sha(raster) or
            not SHA64.fullmatch(str(receipt.get("exe_sha256", "")))):
        raise ValueError("invalid exact original source, executable or log provenance")
    dims = receipt.get("actual_sdl_renderer_output")
    if (not isinstance(dims, list) or len(dims) != 2 or
            any(type(v) is not int for v in dims) or
            not 320 <= dims[0] <= 3840 or not 224 <= dims[1] <= 2160 or
            dims != receipt.get("requested_window_size")):
        raise ValueError("unexpected actual SDL drawable geometry")
    header = (f"P7\nWIDTH {dims[0]}\nHEIGHT {dims[1]}\nDEPTH 4\n"
              "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
    if not raster.startswith(header) or len(raster) != (
            len(header) + dims[0] * dims[1] * 4):
        raise ValueError("truncated or wrong-format real SDL title P7")
    if (b"UR_BALDOSA_MODERN_ROOT opened=1" not in log or
            b"UR_BALDOSA_MODERN_TITLE painted=1" not in log or
            f"output={dims[0]}x{dims[1]} source=SDL_RenderReadPixels".encode() not in log):
        raise ValueError("real native title or SDL readback witness missing")
    is_root = name.endswith("-entered-root")
    if is_root:
        if (b"UR_BALDOSA_MODERN_TITLE entered_root=1" not in log or
                b"UR_BALDOSA_MODERN_ROOT painted=1" not in log):
            raise ValueError("real input-driven title to root handoff absent")
    else:
        if b"UR_BALDOSA_MODERN_TITLE entered_root=1" in log:
            raise ValueError("static title captured a root handoff")
    return receipt, raster[len(header):]


def compare_center_rgb(a: bytes, b: bytes, width: int, height: int) -> dict:
    if len(a) != len(b) or len(a) != width * height * 4:
        raise ValueError("unmatched real SDL title and root pixels")
    # Ignore OS renderer alpha. SDL RGB may be nonblack at alpha zero.
    changed = 0
    nonblack_a = nonblack_b = 0
    min_x = width
    min_y = height
    max_x = max_y = -1
    x0, x1 = width // 5, width * 4 // 5
    y0, y1 = height // 8, height * 4 // 5
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = (y * width + x) * 4
            av, bv = a[p:p+3], b[p:p+3]
            nonblack_a += any(av)
            nonblack_b += any(bv)
            if av == bv:
                continue
            changed += 1
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
    return {
        "changed_rgb_pixels_in_center_roi": changed,
        "center_roi_xyxy": [x0, y0, x1-1, y1-1],
        "difference_bbox_xyxy": ([min_x, min_y, max_x, max_y] if changed else None),
        "title_nonblack_rgb_pixels": nonblack_a,
        "root_nonblack_rgb_pixels": nonblack_b,
    }


def verify(root: Path, source_sha: str) -> dict:
    if not SHA40.fullmatch(source_sha) or root.is_symlink():
        raise ValueError("expected exact native source SHA and real evidence directory")
    receipts, images = {}, {}
    for case in CASES:
        receipts[case], images[case] = load_real_case(root, case, source_sha)
    keys = ("source_sha", "exe_sha256", "observed_in_draw", "SDL_driver",
            "requested_window_size", "actual_sdl_renderer_output")
    for key in keys:
        if len({json.dumps(receipts[name][key]) for name in CASES}) != 1:
            raise ValueError("different original source, PE or drawable across title cases")
    width, height = receipts[CASES[0]]["actual_sdl_renderer_output"]
    normal = compare_center_rgb(images[CASES[0]], images[CASES[1]],
                                width, height)
    reduced = compare_center_rgb(images[CASES[2]], images[CASES[3]],
                                 width, height)
    for label, comparison in (("normal", normal), ("reduced", reduced)):
        if (comparison["changed_rgb_pixels_in_center_roi"] < 300 or
                comparison["title_nonblack_rgb_pixels"] < 300 or
                comparison["root_nonblack_rgb_pixels"] < 300):
            raise ValueError(label + ": real final SDL title or root absent/static")
    return {
        "schema_version": 1,
        "status": "two real native title->root final SDL pixel differences, technical only",
        "source_sha": source_sha,
        "exe_sha256": receipts[CASES[0]]["exe_sha256"],
        "drawable": [width, height],
        "SDL_capture_draw_ordinal": 40,
        "normal": normal,
        "reduced_motion": reduced,
        "source_P6_to_final_SDL_exact_pixel_parity_proven": False,
        "natural_60hz_cadence_proven": False,
        "original_title_visual_design_approved": False,
        "physical_controller_and_display_approved": False,
        "original_guest_CPU_APU_parity_proven": False,
        "release_gate_credit": 0,
        "case_p7_sha256": {name: receipts[name]["p7_sha256"] for name in CASES},
        "case_log_sha256": {
            name: receipts[name]["native_process_log_sha256"] for name in CASES},
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case-root", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        result = verify(a.case_root, a.source_sha)
        if a.output.exists() or a.output.is_symlink():
            raise ValueError("refuse overwrite of original native title receipt")
        a.output.write_text(json.dumps(result, indent=2) + "\n",
                            encoding="utf-8")
        print("REAL_TITLE_ROOT_FINAL_SDL_NATIVE_WITNESS_OK")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("REAL_TITLE_ROOT_FINAL_SDL_NATIVE_WITNESS_REJECTED:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
